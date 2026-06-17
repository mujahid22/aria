# SMS Notification for Order Shipment with Tracking Link

## Overview
This document outlines the technical implementation for an automated SMS notification system that informs customers when their order has shipped. The notification includes the order number and a clickable tracking link for real-time shipment updates.

## Requirements
When an order's status is updated to **'shipped'**, the system must:
1. Automatically trigger an SMS notification to the customer.
2. Include the **order number** and a **clickable tracking link** in the SMS.
3. Direct the customer to the correct **carrier's tracking page** via the link.
4. Log the **SMS delivery status** (success/failure) for auditing.
5. Ensure the notification is sent **only once per shipped order**.

## System Components

### 1. Order Service
- **Responsibility**: Detects when an order status changes to 'shipped'.
- **Trigger**: Publishes an event (e.g., `OrderShippedEvent`) to a message queue or event bus.
- **Data Required**:
  - Order ID
  - Customer phone number
  - Carrier name
  - Tracking number

### 2. Notification Service
- **Responsibility**: Listens for `OrderShippedEvent` and sends the SMS notification.
- **Integration**: Uses an SMS gateway (e.g., Twilio, AWS SNS, or a third-party provider) to send the SMS.
- **SMS Content Template**:
  ```plaintext
  Your order #{order_number} has shipped! Track it here: {tracking_link}
  ```
- **Tracking Link Generation**:
  - Construct the URL using the carrier's tracking domain and the tracking number.
  - Example: `https://www.fedex.com/fedextrack/?trknbr={tracking_number}`

### 3. SMS Gateway
- **Responsibility**: Handles the delivery of SMS messages to customers.
- **Requirements**:
  - Supports API-based SMS sending.
  - Provides delivery status callbacks or webhooks for logging.

### 4. Logging and Auditing
- **Responsibility**: Logs the SMS delivery status (success/failure) for each notification.
- **Data to Log**:
  - Order ID
  - Customer phone number
  - Timestamp of SMS send attempt
  - Delivery status (e.g., `sent`, `delivered`, `failed`)
  - Error details (if applicable)

## Data Flow
1. **Order Status Update**: Order Service updates the order status to 'shipped'.
2. **Event Publication**: Order Service publishes an `OrderShippedEvent`.
3. **Event Consumption**: Notification Service consumes the `OrderShippedEvent`.
4. **SMS Generation**: Notification Service constructs the SMS content using the order details.
5. **SMS Delivery**: Notification Service sends the SMS via the SMS Gateway.
6. **Delivery Confirmation**: SMS Gateway returns the delivery status to the Notification Service.
7. **Logging**: Notification Service logs the delivery status for auditing.

## Implementation Notes
- **Open Questions**:
  - Which SMS gateway will be used (e.g., Twilio, AWS SNS, or another provider)?
  - What is the format of the carrier's tracking URL? Is it consistent across all carriers, or does it vary?
  - Should the system retry failed SMS deliveries? If so, what is the retry policy?
  - Are there any rate limits or throttling requirements for the SMS gateway?
  - How will the system handle phone numbers in different formats (e.g., international numbers)?
  - Is there a need for a fallback mechanism if the SMS gateway fails?

## Testing Requirements
- **Unit Tests**: Verify the logic for generating the tracking link and SMS content.
- **Integration Tests**: Ensure the event flow from Order Service to Notification Service works as expected.
- **End-to-End Tests**: Validate the entire flow, including SMS delivery and logging.
- **Failure Scenarios**: Test cases for failed SMS deliveries and retries (if applicable).

## Deployment Considerations
- **Environment Variables**: Configure SMS gateway credentials and API endpoints.
- **Monitoring**: Set up alerts for failed SMS deliveries.
- **Scalability**: Ensure the Notification Service can handle high volumes of `OrderShippedEvent` events.
