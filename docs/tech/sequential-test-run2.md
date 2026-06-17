# Sequential Test Run 2

## Overview
This document outlines the technical requirements and implementation details for adding a badge to the system. The badge will be displayed in the user interface to indicate a specific status or achievement.

## Requirements
1. **Badge Display**: A badge must be displayed in the user profile section.
2. **Badge Metadata**: The badge must include the following metadata:
   - Name
   - Description
   - Icon (SVG or PNG format)
   - Issued date
3. **Backend Storage**: Badge information must be stored in the database and associated with the user ID.
4. **API Endpoint**: An API endpoint must be created to fetch badge details for a specific user.

## Technical Specifications

### Frontend
- **Component**: Create a new `Badge` React component.
- **Props**: The component should accept the following props:
  - `name` (string)
  - `description` (string)
  - `icon` (string, URL or base64 encoded image)
  - `issuedDate` (string, ISO format)
- **Styling**: Use the existing design system for consistency.

### Backend
- **Database Schema**: Extend the `users` table or create a new `badges` table with the following fields:
  - `id` (primary key)
  - `user_id` (foreign key)
  - `name` (string)
  - `description` (string)
  - `icon` (string, URL or base64 encoded image)
  - `issued_date` (datetime)
- **API Endpoint**: Create a new endpoint `GET /api/users/:userId/badges` that returns the badge details for the specified user.

### Database
- **Migration**: Create a database migration to add the `badges` table or extend the `users` table.
- **Seed Data**: Add seed data for initial badges if required.

## Implementation Notes
- **Open Questions**:
  - Should the badge icon be stored as a URL or directly in the database as a base64 encoded string?
  - What is the expected size limit for the badge icon?
  - Should there be a limit on the number of badges a user can have?
  - Are there any specific design guidelines for the badge component?
- **Dependencies**: Ensure the frontend and backend are updated to handle the new badge data structure.
- **Testing**: Write unit tests for the new `Badge` component and API endpoint.