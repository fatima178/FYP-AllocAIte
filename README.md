# AllocAIte - Staffing Management System for Technical Teams

AllocAIte is a staffing management system for technical teams. It helps managers assign the right employee to the right task using employee data, availability, and AI-supported recommendations. Users can upload an Excel file with employee information, manage tasks, view team availability, generate recommendations, assign work, use a simple chatbot, and update settings.

## Backend

The backend handles the main system logic, database access, recommendation logic, authenticatioand API routes.

### Core Backend Files

- `backend/main.py` - starts the backend API and registers all routes
- `backend/db.py` - connects to the database and creates the database tables

### Backend Routers

- `auth.py` - handles login and registration
- `upload.py` - handles Excel file uploads
- `recommend.py` - handles employee recommendations and task assignment from recommendations
- `tasks.py` - handles task and assignment management
- `dashboard.py` - handles dashboard data
- `chatbot.py` - handles chatbot questions
- `settings.py` - handles user settings
- `employees.py` - handles employee information
- `employee_portal.py` - handles employee portal pages
- `invites.py` - handles employee invite links

### Backend Processing Files

- `upload_processing.py` - reads and stores uploaded employee Excel data
- `assignment_upload_processing.py` - processes uploaded assignment data
- `export_processing.py` - handles exporting data
- `recommend_processing.py` - creates ranked employee recommendations
- `recommend_assignment.py` - assigns a recommended employee to a task
- `recommendation_log_processing.py` - stores recommendation history
- `task_matching.py` - compares tasks with employee skills and experience
- `task_scoring.py` - scores and ranks employees
- `task_processing.py` - manages task logic
- `task_data_access.py` - gets task data from the database
- `dashboard_processing.py` - prepares dashboard data
- `availability_processing.py` - checks employee availability
- `chatbot_processing.py` - handles chatbot logic
- `settings_processing.py` - updates user settings
- `weight_defaults.py` - stores default recommendation weight settings
- `invite_processing.py` - handles invite logic
- `assignment_history_processing.py` - handles assignment history
- `employee_processing.py` - handles employee data
- `employee_calendar_processing.py` - handles employee calendar data
- `employee_profile_read_processing.py` - loads employee profile data
- `employee_profile_skills_processing.py` - handles employee skills
- `employee_profile_preferences_processing.py` - handles employee preferences
- `employee_profile_common.py` - shared employee profile logic

### Backend Schema Files

- `recommend.py` - defines recommendation data format
- `settings.py` - defines settings data format
- `employee_portal.py` - defines employee portal data format

### Backend Utility Files

- `auth_utils.py` - helper functions for authentication
- `request_utils.py` - helper functions for API requests

## Frontend

The frontend handles the user interface and allows managers and employees to interact with the system.

### Main Frontend Files

- `App.js` - controls which page is shown
- `index.js` - starts the frontend app
- `api.js` - stores API calls to the backend
- `session.js` - stores user session information
- `preferences.js` - handles saved display preferences
- `navigation.js` - handles navigation links
- `formatters.js` - formats values shown in the app
- `recommendationSession.js` - stores recommendation session data

### Frontend Pages

- `Login.jsx` - login and register page
- `Menu.jsx` - navigation menu
- `UploadPage.jsx` - upload employee Excel data
- `AssignmentsPage.jsx` - enter a task and request recommendations
- `RecommendationsPage.jsx` - view ranked employees and assign a task
- `DashboardPage.jsx` - view employee availability and workload
- `TasksPage.jsx` - manage tasks and assignments
- `ChatbotPage.jsx` - ask staffing-related questions
- `ChatbotPopup.jsx` - floating chatbot popup
- `SettingsPage.jsx` - update profile, display settings, and system settings
- `InvitePage.jsx` - employee invite page
- `EmployeePortalPage.jsx` - employee portal main page
- `EmployeeCalendarPage.jsx` - employee calendar page
- `EmployeeSettingsPage.jsx` - employee settings page

### Frontend Dashboard Files

- `EmployeeGrid.jsx` - displays employees on the dashboard
- `FiltersBar.jsx` - filters dashboard results
- `SkillApprovalPanel.jsx` - shows skill approval requests
- `SummaryCards.jsx` - shows dashboard summary cards
- `useDashboardState.js` - stores dashboard page logic

### Frontend Task Files

- `TaskFormModal.jsx` - form for creating or editing tasks
- `TasksCalendar.jsx` - calendar view for tasks
- `CompletedTasksPanel.jsx` - shows completed tasks
- `FeedbackModal.jsx` - handles task feedback
- `utils.js` - helper functions for tasks

### Frontend Settings Files

- `AccountSection.jsx` - account settings
- `AppearanceSection.jsx` - theme and font settings
- `EditDetailsModal.jsx` - edit user details popup
- `ExportSection.jsx` - export settings and data
- `HistorySection.jsx` - shows history
- `PasswordModal.jsx` - change password popup
- `SectionSidebar.jsx` - settings sidebar
- `TeamSection.jsx` - team settings
- `WeightsSection.jsx` - recommendation weight settings
- `useSettingsState.js` - stores settings page logic
- `constants.js` - stores settings values

### Frontend Employee Portal Files

- `ProfileTab.jsx` - employee profile section
- `WorkTab.jsx` - employee work section
- `GrowthTab.jsx` - employee growth section

## Workflow

1. The user registers or logs in
2. The user uploads an Excel file with employee data
3. The backend validates and stores the data
4. The user enters a task
5. The system recommends the best employees
6. The user assigns the task
7. The dashboard updates workload and availability
8. The chatbot can answer simple staffing questions
9. The user can update settings when needed
