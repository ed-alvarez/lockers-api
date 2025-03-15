from util import email
from routes.white_label.model import WhiteLabel
from routes.issue.model import Issue

from ...organization.controller import get_org_sendgrid_auth_sender, is_ups_org


def load_email_template(org_name, white_label: WhiteLabel, issue: Issue.Read):
    from pathlib import Path

    ROOT_DIR = Path(__file__).parent
    psub_file = ROOT_DIR / "email_message.html"

    with open(psub_file) as f:
        contents = f.read()
        default_logo = "https://assets.website-files.com/61f7e37730d06c4a05d2c4f3/62c640ed55a520a3d21d9b61_koloni-logo-black%207-p-500.png"

        return (
            contents.replace("{{org_name}}", white_label.app_name)
            .replace(
                "{{org_logo}}",
                white_label.app_logo if white_label.app_logo else default_logo,
            )
            .replace("{{org_url}}", f"https://{org_name}.koloni.io")
            .replace("{{app_name}}", white_label.app_name)
            .replace("{{issue_id}}", issue.issue_id)
            .replace("{{created_at}}", str(issue.created_at))
            .replace("{{issue_description}}", issue.description)
        )


async def email_issue_to_support(
    org_default_support_email, location_email, issue: Issue.Read, id_org
):
    email_sender = await get_org_sendgrid_auth_sender(id_org)

    email.send(
        sender=email_sender,
        recipient=location_email if location_email else org_default_support_email,
        subject=f"New issue reported - {issue['issue_id']}",
        html_content=f"<strong>Issue ID:</strong> {issue['issue_id']}<br />"
        + f"<strong>Created At:</strong> {issue['created_at']}<br />"
        + f"<strong>Issue Description:</strong> {issue['description']}<br />",
        is_ups_org=await is_ups_org(id_org),
    )


async def email_notify_team_member(
    org_name, team_member_email, white_label: WhiteLabel, issue: Issue.Read, id_org
):
    email_sender = await get_org_sendgrid_auth_sender(id_org)

    email.send(
        sender=email_sender,
        recipient=team_member_email,
        subject=f"New issue assigned to you - {issue.issue_id}",
        html_content=load_email_template(org_name, white_label, issue),
        is_ups_org=await is_ups_org(id_org),
    )
