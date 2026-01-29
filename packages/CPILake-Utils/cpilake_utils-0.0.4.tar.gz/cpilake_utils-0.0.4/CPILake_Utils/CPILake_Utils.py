import re
import json
import time
import pytz
import html
import base64
import requests
import pandas as pd
from pyspark.sql                                import SparkSession
from pyspark.sql                                import DataFrame, functions as F
from pyspark.sql.functions                      import unix_timestamp, col, max, from_utc_timestamp
from pyspark.conf                               import SparkConf
from datetime                                   import datetime
from typing                                     import Optional, List, Dict, Tuple, Union

## <<<<<<<<<<<<<<<<         hash_function 

def hash_function(s):
    """Hash function for alphanumeric strings"""
    if s is None:
        return None
    s = str(s).upper()
    s = re.sub(r'[^A-Z0-9]', '', s)
    base36_map = {ch: idx for idx, ch in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
    result = 0
    for i, ch in enumerate(reversed(s)):
        result += base36_map.get(ch, 0) * (36 ** i)
    result += len(s) * (36 ** (len(s) + 1))
    return result

## <<<<<<<<<<<<<<<<         send_email_via_http 

def send_email_via_http(
    body:                       str,
    to:                         List[str],
    tenant_id:                  str,
    client_id:                  str,
    certificate_secret_name:    str,
    keyvault_url:               str,
    df_in_body:                 bool,
    df_attach:                  bool,  
    endpoint_url:               Optional[str] = None,
    scope:                      Optional[str] = None,
    subject:                    Optional[str] = None,
    headers:                    Optional[Dict[str, str]] = None,
    timeout:                    int = 15
) -> Tuple[Optional[int], str]:
    
    import base64
    import requests
    from notebookutils.credentials  import getSecret
    from azure.identity             import CertificateCredential
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("send_email_via_http").getOrCreate()

    tenant_id                   =   spark.conf.get("spark.tenantid")
    client_id                   =   spark.conf.get("spark.clientid")
    certificate_secret_name     =   spark.conf.get("spark.certname")
    keyvault_url                =   spark.conf.get("spark.vaultname")

    # Defaults
    endpoint_url = (
            "https://fdne-inframail-logicapp01.azurewebsites.net:443/"
            "api/fdne-infra-appmail-sender/triggers/"
            "When_a_HTTP_request_is_received/invoke"
            "?api-version=2022-05-01" )

    scope = "api://27d45411-0d7a-4f27-bc5f-412d74ea249b/.default"

    # Credential
    secret_value = getSecret(keyvault_url, certificate_secret_name)
    certificate_data = base64.b64decode(secret_value)

    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_data=certificate_data,
        send_certificate_chain=True
    )

    access_token = credential.get_token(scope).token

    params = {
    "body":         body,
    "to":           to,
    "subject":      subject,
    "df_in_body":   df_in_body,
    "df_attach":    df_attach,
    "headers":      headers,
    "timeout":      timeout}

    # Required checks
    required = ['to', 'subject', 'body']
    missing = [f for f in required if not params.get(f)]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    # Base payload
    payload = {
        "to": ";".join(params["to"]) if isinstance(params["to"], list) else params["to"],
        "subject": params["subject"],
        "body": params["body"],
    }
    if params.get("cc"):
        payload["cc"] = params["cc"] if isinstance(params["cc"], list) else [params["cc"]]
    if params.get("bcc"):
        payload["bcc"] = params["bcc"] if isinstance(params["bcc"], list) else [params["bcc"]]
    if params.get("from_addr"):
        payload["from"] = params["from_addr"]
    if params.get("attachments"):
        payload["attachments"] = params["attachments"]

    # ---- DataFrame → HTML body (your existing style) ----
    df = params.get("df")
    if df is not None:
        df_limit = int(params.get("df_limit", 1000))
        tz_name  = params.get("tz_name", "America/Los_Angeles")
        df_in_body = params.get("df_in_body", True)
        df_attach  = params.get("df_attach", False)
        df_name    = params.get("df_name", "data.html")

        # Get pandas DataFrame
        pdf = None
        try:
            from pyspark.sql import DataFrame as SparkDF
            if isinstance(df, SparkDF):
                pdf = df.limit(df_limit).toPandas()
            else:
                pdf = df  # assume already pandas
        except Exception:
            pdf = df

        html_body = _df_to_html_table(pdf, tz_name=tz_name)

        if df_in_body:
            subject = str(params.get("subject", ""))
            if "QA Success" in subject:
                payload["body"] ='<html><body><h4>No data available to display.</h4></body></html>'
            else:
                payload["body"] = html_body
        else:
            # append to body if you prefer not to replace
            payload["body"] = f'{payload["body"]}{html_body}'

        if df_attach:
            content_b64 = base64.b64encode(html_body.encode("utf-8")).decode("utf-8")
            attach = {"name": df_name, "contentBytes": content_b64, "contentType": "text/html"}
            if "attachments" in payload and isinstance(payload["attachments"], list):
                payload["attachments"].append(attach)
            else:
                payload["attachments"] = [attach]

    # Auth header
    req_headers = {"Authorization": f"Bearer {access_token}"}
    if params.get("headers"):
        req_headers.update(params["headers"])

    timeout = params.get("timeout", 15)

    # Send
    try:
        response = requests.post(endpoint_url, json=payload, headers=req_headers, timeout=timeout)
        status_msg = "Success" if response.status_code == 200 else f"Failed ({response.status_code})"
        print(f"Email send: {status_msg}")
        return response.status_code, response.text, req_headers
    except requests.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"{error_msg}")
        return None, error_msg
"""
# call the function
    status, response, req_headers  = send_email_via_http(
        body                    =   body_html,
        to                      =   RECIPIENTS,
        subject                 =   subject,
        tenant_id               =   tenant_id,
        client_id               =   client_id,
        certificate_secret_name =   certificate_secret_name,
        keyvault_url            =   keyvault_url,
        df_in_body              =   False,
        df_attach               =   False    )
"""

## <<<<<<<<<<<<<<<<         _df_to_html_table

def _df_to_html_table(pdf, tz_name="America/Los_Angeles"):
    """Render a pandas DataFrame to your styled HTML table."""
    # Empty DF → simple message
    if pdf is None or len(pdf.index) == 0:
        return '<html><body><h4>No data available to display.</h4></body></html>'

    # Header with PST time
    pst = pytz.timezone(tz_name)
    now_pst = datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S")

    html_Table = []
    html_Table.append('<html><head><style>')
    html_Table.append('table {border-collapse: collapse; width: 100%} '
                      'table, td, th {border: 1px solid black; padding: 3px; font-size: 9pt;} '
                      'td, th {text-align: left;}')
    html_Table.append('</style></head><body>')
    html_Table.append(f'<h4>(Refresh Time: {now_pst})</h4><hr>')
    html_Table.append('<table style="width:100%; border-collapse: collapse;">')
    html_Table.append('<thead style="background-color:#000000; color:#ffffff;"><tr>')

    # Columns (skip FailureFlag in header, to match your code)
    cols = list(pdf.columns)
    visible_cols = [c for c in cols if c != "FailureFlag"]
    for c in visible_cols:
        html_Table.append(f'<th style="border: 1px solid black; padding: 5px;">{html.escape(str(c))}</th>')
    html_Table.append('</tr></thead><tbody>')

    # Rows (highlight red if FailureFlag == 'Yes', else light green default)
    ff_present = "FailureFlag" in cols
    for _, row in pdf.iterrows():
        row_bg_color = '#ccff66'  # default
        if ff_present:
            try:
                if str(row["FailureFlag"]).strip().lower() == "yes":
                    row_bg_color = '#ff8080'
            except Exception:
                pass
        html_Table.append(f'<tr style="background-color:{row_bg_color};">')
        for c in visible_cols:
            val = row[c]
            html_Table.append(f'<td>{html.escape("" if val is None else str(val))}</td>')
        html_Table.append('</tr>')

    html_Table.append('</tbody></table></body></html>')
    return "".join(html_Table)

# s<<<<<<<<<<<          end_email_no_attachment

def send_email_no_attachment(
    body:                       str,
    recipients:                 List[str],
    tenant_id:                  str,
    client_id:                  str,
    certificate_secret_name:    str,
    keyvault_url:               str,
    endpoint_url:               Optional[str] = None,
    scope:                      Optional[str] = None,
    subject:                    Optional[str] = None,
    headers:                    Optional[Dict[str, str]] = None,
    timeout:                    int = 15
) -> Tuple[Optional[int], str]:

    import base64
    import requests
    from notebookutils.credentials  import getSecret
    from azure.identity             import CertificateCredential
    
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("send_email_no_attachment").getOrCreate()

    tenant_id                   =   spark.conf.get("spark.tenantid")
    client_id                   =   spark.conf.get("spark.clientid")
    certificate_secret_name     =   spark.conf.get("spark.certname")
    keyvault_url                =   spark.conf.get("spark.vaultname")

    # Defaults
    endpoint_url = (
            "https://fdne-inframail-logicapp01.azurewebsites.net:443/"
            "api/fdne-infra-appmail-sender/triggers/"
            "When_a_HTTP_request_is_received/invoke"
            "?api-version=2022-05-01" )

    scope = "api://27d45411-0d7a-4f27-bc5f-412d74ea249b/.default"

    # Payload
    payload = {
        "to": ";".join(recipients),
        "subject": subject or "",
        "body": body, }

    # Credential
    secret_value = getSecret(keyvault_url, certificate_secret_name)
    certificate_data = base64.b64decode(secret_value)

    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_data=certificate_data,
        send_certificate_chain=True
    )

    access_token = credential.get_token(scope).token

    # Headers
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        **(headers or {}),
    }

    # Call API
    try:
        resp = requests.post(
            endpoint_url,
            json=payload,
            headers=request_headers,
            timeout=timeout,
        )

        if resp.status_code in (200, 201, 202):
            return resp.status_code, resp.text

        return resp.status_code, f"Failed: {resp.text}"

    except requests.RequestException as e:
        return None, str(e)
"""
# call the function
status, response = send_email_no_attachment(
    body=markdown,
    recipients=recipients,
    subject=subject,
    tenant_id=tenant_id,
    client_id=client_id,
    certificate_secret_name =   certificate_secret_name,
    keyvault_url=keyvault_url
)
"""

# >>>>>>>>>>>>>>>>>          end_email_no_attachment

## <<<<<<<<<<<<<<<<         QA_CheckUtil
"""
A status column: PASS / FAIL / SKIPPED
A skip_reason column
Checks are skipped instead of failing when:
    One or both DataFrames are empty
    Required columns are missing
    Aggregation column exists but contains only nulls
    match becomes None when skipped (clearer than False)
"""
def QA_CheckUtil(
    source_df: DataFrame,
    qa_df: DataFrame
) -> DataFrame:

    spark = source_df.sparkSession
    qa_rows: List[tuple] = []

    def calc_diff(src, qa):
        if src is None or qa is None:
            return None
        return float(src) - float(qa)

    def add_row(check_type, check_name, column, src, qa, skip_reason=None):
        if skip_reason:
            qa_rows.append((
                check_type,
                check_name,
                column,
                src,
                qa,
                None,
                None,
                "SKIPPED",
                skip_reason
            ))
        else:
            match = src == qa
            qa_rows.append((
                check_type,
                check_name,
                column,
                src,
                qa,
                calc_diff(src, qa),
                match,
                "PASS" if match else "FAIL",
                None
            ))

    # Row count
    src_count   = source_df.count()
    qa_count    = qa_df.count()

    add_row(
        "ROW_COUNT",
        "row_count",
        None,
        float(src_count),
        float(qa_count)
    )

    # Null check
    common_cols = set(source_df.columns).intersection(set(qa_df.columns))

    if not common_cols:
        add_row(
            "NULL_CHECK",
            "null_count",
            None,
            None,
            None,
            "No common columns between source and QA"
        )
    else:
        for col in common_cols:
            src_nulls = source_df.filter(F.col(col).isNull()).count()
            qa_nulls = qa_df.filter(F.col(col).isNull()).count()

            add_row(
                "NULL_CHECK",
                "null_count",
                col,
                float(src_nulls),
                float(qa_nulls)
            )


    # Aggregation check
    if "amount" not in source_df.columns or "amount" not in qa_df.columns:
        add_row(
            "AGG_CHECK",
            "sum",
            "amount",
            None,
            None,
            "Column 'amount' missing in one or both DataFrames"
        )
    else:
        src_sum = source_df.select(F.sum("amount")).collect()[0][0]
        qa_sum = qa_df.select(F.sum("amount")).collect()[0][0]

        if src_sum is None and qa_sum is None:
            add_row(
                "AGG_CHECK",
                "sum",
                "amount",
                None,
                None,
                "All values are NULL in both DataFrames"
            )
        else:
            add_row(
                "AGG_CHECK",
                "sum",
                "amount",
                float(src_sum or 0.0),
                float(qa_sum or 0.0)
            )


    # Duplicate check on id column
    if "id" not in source_df.columns or "id" not in qa_df.columns:
        add_row(
            "DUPLICATE_CHECK",
            "duplicate_id",
            "id",
            None,
            None,
            "Column 'id' missing in one or both DataFrames"
        )
    else:
        src_dupes = source_df.count() - source_df.select("id").distinct().count()
        qa_dupes = qa_df.count() - qa_df.select("id").distinct().count()

        add_row(
            "DUPLICATE_CHECK",
            "duplicate_id",
            "id",
            float(src_dupes),
            float(qa_dupes)
        )

    # Create final QA DataFrame
    return spark.createDataFrame(
        qa_rows,
        [
            "check_type",
            "check_name",
            "column_name",
            "source_value",
            "qa_value",
            "diff",
            "match",
            "status",
            "skip_reason"
        ]
    )

## <<<<<<<<<<<<<<<<         create_lakehouse_shortcuts MI

def create_lakehouse_shortcuts(shortcut_configs):
    import requests, json
    import sempy.fabric as fabric
    from notebookutils.credentials import getToken

    access_token = getToken("https://api.fabric.microsoft.com/.default")

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json" }

    workspace_id = fabric.get_notebook_workspace_id()
    lakehouse_id = fabric.get_lakehouse_id()

    for config in shortcut_configs:
        source_path             =   config["source_subpath"]
        target_schema           =   config["target_schema"]
        target_shortcut_name    =   config["target_shortcut_name"]
        target_path             =   f"Tables/{target_schema}/"

        payload = {
            "path": target_path,
            "name": target_shortcut_name,
            "target": {
                "type": "OneLake",
                "oneLake": {
                    "workspaceId"   :   workspace_id,
                    "itemId"        :   lakehouse_id,
                    "path"          :   source_path,
                    "target_schema" :   config["target_schema"]
                }
            }
        }

        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"
        print(f"Creating shortcut '{target_shortcut_name}' → {target_path}")
        print(json.dumps(payload, indent=2))

        # --- Send POST request ---
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"Shortcut '{target_shortcut_name}' created successfully.")
            print(response.json())
        else:
            print(f"Failed to create shortcut '{target_shortcut_name}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

"""
# How to call function

target_schema       =   spark.conf.get("spark.CostHubSchema")

shortcut_configs = [  
    {
        "target_shortcut_name"  :   "DIM_Date_01",
        "source_subpath"        :   "Tables/CostHub/DIM_Date",
        "target_schema"         :   target_schema,
        "target_path"           :   "Tables/CostHub/"
    }
]
create_lakehouse_shortcuts(shortcut_configs)
"""

## <<<<<<<<<<<<<<<<         create_adls_shortcuts with MI

def create_adls_shortcuts(shortcut_configs):

    import requests
    import sempy.fabric as fabric
    from notebookutils.credentials import getToken
    
    access_token = getToken("https://api.fabric.microsoft.com/.default")

    headers = {        "Authorization": f"Bearer {access_token}",        "Content-Type": "application/json"    }

    workspace_id = fabric.get_notebook_workspace_id()
    lakehouse_id = fabric.get_lakehouse_id()

    for config in shortcut_configs:
        target_schema       = config["target_schema"]
        connection_name     = config["connection_name"]
        target_path         = f"Tables/{target_schema}/"

    resp_cn         = requests.get(f"https://api.fabric.microsoft.com/v1/connections", headers=headers)
    connection_id   = next(conn["id"] for conn in resp_cn.json()["value"] if conn["displayName"] == connection_name)
    conn_loc        = next(conn for conn in resp_cn.json()["value"] if conn["displayName"] == connection_name)
    location        = conn_loc["connectionDetails"]["path"]

    for config in shortcut_configs:
        payload = {
            "name": config["name"],
            "path": target_path,
            "target": {
                "type": "AdlsGen2",
                "adlsGen2": {
                    "connectionId": connection_id,
                    "location": location,
                    "subpath": config["subpath"]                }            }        }

        url = (f"https://api.fabric.microsoft.com/v1/workspaces/"
            f"{workspace_id}/items/{lakehouse_id}/shortcuts"        )

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in (200, 201):
            print(f"Shortcut '{config['name']}' created successfully.")
        else:
            print(f"Failed to create shortcut '{config['name']}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

"""
# How to call function

target_workspace_id =   spark.conf.get("spark.workspaceid")
target_lakehouse_id =   spark.conf.get("spark.lakehouseid")
target_schema       =   spark.conf.get("spark.CostHubSchema")
target_location     =   spark.conf.get("spark.adlslocation")
target_connection   =   spark.conf.get("spark.connectionid")

# Define shortcut configurations
shortcut_configs = [
    {
        "name"              :   "Z-RefreshTime_01",
        "target_schema"     :   target_schema,
        "connection_name"   :   "CostHub_ADLS abibrahi",
        "target_path"       :   f"Tables/{target_schema}/",
        "subpath"           :   "/abidatamercury/MercuryDataProd/CostHub/Bridge_ExecOrgSummary"
    }]

# Call the function
create_adls_shortcuts(shortcut_configs)  

"""


## <<<<<<<<<<<<<<<<         create_adls_shortcuts with SPN

def create_adls_shortcuts_spn(shortcut_configs):

    import base64
    import requests
    from notebookutils.credentials import getSecret
    from azure.identity import CertificateCredential

    tenant_id               = spark.conf.get("spark.tenantid")
    client_id               = spark.conf.get("spark.clientid")
    certificate_secret_name = spark.conf.get("spark.certname")
    keyvault_url            = spark.conf.get("spark.vaultname")

    # Fabric scope
    scope = "https://api.fabric.microsoft.com/.default"

    # Get certificate from Key Vault
    secret_value = getSecret(keyvault_url, certificate_secret_name)
    certificate_data = base64.b64decode(secret_value)

    # Create credential
    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_data=certificate_data,
        send_certificate_chain=True    )

    # Get access token
    access_token = credential.get_token(scope).token
    
    # access_token = getToken("https://api.fabric.microsoft.com/.default")

    headers = {        "Authorization": f"Bearer {access_token}",        "Content-Type": "application/json"    }

    workspace_id = fabric.get_notebook_workspace_id()
    lakehouse_id = fabric.get_lakehouse_id()

    for config in shortcut_configs:
        target_schema       = config["target_schema"]
        connection_name     = config["connection_name"]
        target_path         = f"Tables/{target_schema}/"

    resp_cn         = requests.get(f"https://api.fabric.microsoft.com/v1/connections", headers=headers)
    connection_id   = next(conn["id"] for conn in resp_cn.json()["value"] if conn["displayName"] == connection_name)
    conn_loc        = next(conn for conn in resp_cn.json()["value"] if conn["displayName"] == connection_name)
    location        = conn_loc["connectionDetails"]["path"]

    for config in shortcut_configs:
        payload = {
            "name": config["name"],
            "path": target_path,
            "target": {
                "type": "AdlsGen2",
                "adlsGen2": {
                    "connectionId": connection_id,
                    "location": location,
                    "subpath": config["subpath"]                }            }        }

        url = (f"https://api.fabric.microsoft.com/v1/workspaces/"
            f"{workspace_id}/items/{lakehouse_id}/shortcuts"        )

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in (200, 201):
            print(f"Shortcut '{config['name']}' created successfully.")
        else:
            print(f"Failed to create shortcut '{config['name']}'.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

"""
# How to call function

target_workspace_id =   spark.conf.get("spark.workspaceid")
target_lakehouse_id =   spark.conf.get("spark.lakehouseid")
target_schema       =   spark.conf.get("spark.CostHubSchema")
target_location     =   spark.conf.get("spark.adlslocation")
target_connection   =   spark.conf.get("spark.connectionid")

# Define shortcut configurations
shortcut_configs = [
    {
        "name"              :   "Z-RefreshTime_01",
        "target_schema"     :   target_schema,
        "connection_name"   :   "CostHub_ADLS abibrahi",
        "target_path"       :   f"Tables/{target_schema}/",
        "subpath"           :   "/abidatamercury/MercuryDataProd/CostHub/Bridge_ExecOrgSummary"
    }]

# Call the function
create_adls_shortcuts_spn(shortcut_configs)  

"""
 
## <<<<<<<<<<<<<<<<         lakehouse_metadata_sync 

import time
import sempy.fabric as fabric

def pad_or_truncate_string(input_string, length, pad_char=' '):
    if len(input_string) > length:
        return input_string[:length]
    return input_string.ljust(length, pad_char)


def lakehouse_metadata_sync(workspace_id, lakehouse_id):
    client = fabric.FabricRestClient()

    # Get lakehouse properties
    lakehouse_props = client.get(
        f"/v1/workspaces/{workspace_id}/lakehouses/{lakehouse_id}"
    ).json()

    sqlendpoint = lakehouse_props["properties"]["sqlEndpointProperties"]["id"]

    uri = f"/v1.0/myorg/lhdatamarts/{sqlendpoint}"
    payload = {
        "commands": [
            {"$type": "MetadataRefreshExternalCommand"}
        ]
    }

    try:
        response = client.post(uri, json=payload)
        response_data = response.json()

        batchId = response_data["batchId"]
        progressState = response_data["progressState"]

        statusuri = f"/v1.0/myorg/lhdatamarts/{sqlendpoint}/batches/{batchId}"

        # Poll status
        while progressState == "inProgress":
            time.sleep(2)
            status_response = client.get(statusuri).json()
            progressState = status_response["progressState"]
            print(f"Sync state: {progressState}")

        if progressState == "success":
            table_details = [
                {
                    "tableName": t["tableName"],
                    "warningMessages": t.get("warningMessages", []),
                    "lastSuccessfulUpdate": t.get("lastSuccessfulUpdate", "N/A"),
                    "tableSyncState": t["tableSyncState"],
                    "sqlSyncState": t["sqlSyncState"],
                }
                for t in status_response["operationInformation"][0]
                ["progressDetail"]["tablesSyncStatus"]
            ]

            print("✅ Extracted Table Details:")
            for detail in table_details:
                print(
                    f"Table: {pad_or_truncate_string(detail['tableName'], 30)}"
                    f" | Last Update: {detail['lastSuccessfulUpdate']}"
                    f" | tableSyncState: {detail['tableSyncState']}"
                    f" | Warnings: {detail['warningMessages']}"
                )

            return {"status": "success", "details": table_details}

        elif progressState == "failure":
            print("❌ Metadata sync failed.")
            return {"status": "failure", "error": status_response}

        else:
            print(f"⚠️ Unexpected progress state: {progressState}")
            return {"status": "unknown", "raw_response": status_response}

    except Exception as e:
        print("🚨 Error during metadata sync:", str(e))
        return {"status": "exception", "error": str(e)}

    
"""
# How to call function ( lakehouse_metadata_sync )
workspace_id = spark.conf.get("trident.workspace.id")
lakehouse_id = spark.conf.get("trident.lakehouse.id")

# Call the function
result = lakehouse_metadata_sync(workspace_id, lakehouse_id)
display(result)
"""
