from datetime import datetime
from typing import List

from ul_api_utils.resources.health_check.health_check import HealthCheckResult


def render_result_row(result: HealthCheckResult, lvl: int) -> str:
    table_s = ''
    td_s = ''
    td_s += f'<td>{"->&nbsp;" * lvl}{result.name}</td>'
    td_s += f'<td>{result.status.name}</td>'
    td_s += f'<td>{result.time_spent: <4.3f}s</td>'
    td_s += f'<td><pre style="display: block; padding: 0; margin: 0;">' \
            f'<code style="display: block; padding: 0; margin: 0;">{result.info if result.info is not None else "-"}</code></pre></td>'
    table_s += f'<tr class="status-{result.status.name.lower()}">{td_s}</tr>'
    if result.internal_health_check_results:
        for res in result.internal_health_check_results:
            table_s += render_result_row(res, lvl + 1)
    return table_s


def generate_health_check_table(health_check_results: List[HealthCheckResult], service_name: str) -> str:
    header_s = f'''<!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>Health Check</title>
    </head>
    <body>
    <div class="container">
    <h1>Health Check Results {service_name} ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})</h1>
    '''
    footer_s = '''
        </div>
        <style>
            .container { max-width: 1024px; margin: 30vh auto 100px; font-family: monospace; font-size: 14px; line-height: 1.2; }
            table { border-collapse: collapse; width: 100%; background: white; }
            table th { padding: 2px 4px; }
            table td { padding: 2px 4px; border: 1px solid #ccc; }
            table tr.status-ok > td { background: #a7ffa7; }
            table tr.status-warn > td { background: yellow; }
            table tr.status-has_errors > td { background: #f7abab; }
        </style>
        </body>
    </html>
    '''

    table_s = '<table>' \
              '<thead>' \
              '<tr>' \
              '<th align="left">Name of Test</th>' \
              '<th align="left">Status</th>' \
              '<th align="left">Duration</th>' \
              '<th align="left">Info</th>' \
              '</tr>' \
              '</thead>' \
              '<tbody>'
    for result in health_check_results:
        table_s += render_result_row(result, 0)

    table_s += '</tbody></table>'
    return header_s + table_s + footer_s
