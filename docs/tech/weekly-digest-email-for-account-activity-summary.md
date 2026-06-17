# Weekly Digest Email for Account Activity Summary
## Overview
This Business Requirements Document (BRD) outlines the implementation of a weekly digest email feature for ARIA. The goal is to provide users with a summarized view of their account activity over the past week, ensuring they stay informed about key metrics, updates, and actions taken. This feature targets users who have been active in the past 30 days and aims to improve engagement and transparency.
## Description
The weekly digest email will be automatically generated and sent to users who have performed at least one action in the past 30 days. The email will include:
- A summary of key metrics, such as the number of logins, actions completed, or other relevant activity.
- A clear breakdown of notable updates or changes to the user\'s account or related data.
- A call-to-action (e.g., \'View Full Activity\' link) redirecting users to a detailed activity page.
The email will be sent every Monday at 9:00 AM in the user\'s local time zone. The system must handle edge cases such as bounce backs and unsubscribes gracefully to ensure a seamless experience.
## Acceptance Criteria
- The email must be sent every Monday at 9:00 AM (user\'s local time).
- The email must only be sent to users who performed at least one action in the past 30 days.
- The email must include a summary of key metrics (e.g., number of logins, actions completed, or other relevant activity).
- The email must provide a clear breakdown of notable updates or changes to the user\'s account or related data.
- The email must include a call-to-action (e.g., \'View Full Activity\' link) redirecting to a detailed activity page.
- The system must handle bounce backs and unsubscribes gracefully without breaking the email delivery process.
## Priority
Medium
## Implementation Notes
- How will the system determine the user\'s local time zone?
- What is the expected format of the summary of key metrics and notable updates?
- How will the system handle cases where the user has not performed any actions in the past 30 days?