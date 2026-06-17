# Implement SMS-based Two-Factor Authentication for Customer Login
## Overview
This Business Requirements Document (BRD) outlines the implementation of SMS-based Two-Factor Authentication (2FA) for customer login. The goal is to enhance security by requiring users to provide a one-time code sent via SMS after entering their credentials. This feature will be rolled out as an optional setting initially but will be enabled by default for high-risk login attempts.
## Description
To improve the security of customer accounts, ARIA will implement SMS-based Two-Factor Authentication (2FA). After entering their username and password, users will be required to input a 6-digit one-time code sent to their registered phone number. This additional layer of security will help prevent unauthorized access, especially in high-risk scenarios such as logins from new devices or locations.
## Acceptance Criteria
- Users must receive an SMS with a 6-digit one-time code within 30 seconds of requesting it during login.
- The system must validate the one-time code entered by the user and grant access only if the code is correct.
- Users must be able to request a new one-time code if the previous one expires or is not received.
- The 2FA setup must be optional during initial rollout but enabled by default for high-risk login attempts (e.g., new device or location).
- The system must log 2FA attempts and failures for security monitoring and auditing.
- The solution must comply with telecom regulations (e.g., GDPR, TCPA) and not send unsolicited messages.
## Priority
High
## Implementation Notes
- How will the system handle cases where the user’s phone number is not registered or is invalid?
- What is the mechanism for requesting a new one-time code if the previous one expires or is not received?
- How will the system ensure compliance with telecom regulations (e.g., GDPR, TCPA)?