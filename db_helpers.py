import os
import psycopg2

def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USERNAME'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    return connection


def consolidate_comments_in_reports(reports_with_comments):
    print(reports_with_comments)
    consolidated_reports = []
    for report in reports_with_comments:
        # Check if this report has already been added to consolidated_reports
        report_exists = False
        for consolidated_report in consolidated_reports:
            if report["id"] == consolidated_report["id"]:
                report_exists = True
                consolidated_report["comments"].append(
                    {"comment_text": report["comment_text"],
                     "comment_id": report["comment_id"],
                     "comment_author_username": report["comment_author_username"]
                    })
                break

        # If the report doesn't exist in consolidated_reports, add it
        if not report_exists:
            report["comments"] = []
            if report["comment_id"] is not None:
                report["comments"].append(
                    {"comment_text": report["comment_text"],
                     "comment_id": report["comment_id"],
                     "comment_author_username": report["comment_author_username"]
                    }
                )
            del report["comment_id"]
            del report["comment_text"]
            del report["comment_author_username"]
            consolidated_reports.append(report)

    return consolidated_reports

