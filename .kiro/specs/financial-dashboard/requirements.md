# Requirements Document

## Introduction

This document specifies the requirements for a Financial Reporting Dashboard that displays Vietnamese financial statements (Balance Sheet, Income Statement, and Cash Flow Statement) from a PostgreSQL database. The system shall provide an interactive web interface allowing users to view and analyze financial data across multiple time periods with configurable display options.

## Glossary

- **Dashboard**: The web-based user interface for viewing financial reports
- **Financial Statement**: A formal record of financial activities (Balance Sheet, Income Statement, or Cash Flow Statement)
- **Stock Symbol**: A unique identifier for a company (e.g., BIC, PGI, BMI)
- **Quarter**: A three-month period in a fiscal year (Q1, Q2, Q3, Q4)
- **Display Unit**: The numerical scale for displaying financial figures (e.g., 1, 1,000, 1,000,000)
- **Indicator**: A specific financial metric or line item in a financial statement
- **Hierarchy Level**: The depth of nesting for financial indicators (parent/child relationships)
- **PostgreSQL Database**: The data storage system containing financial statement data in JSONB format
- **API Backend**: The FastAPI server that provides data access endpoints
- **Frontend**: The HTML/CSS/JavaScript interface that users interact with

## Requirements

### Requirement 1: Database Connection and Data Retrieval

**User Story:** As a system administrator, I want the Dashboard to connect to the PostgreSQL database, so that financial data can be retrieved and displayed to users.

#### Acceptance Criteria

1. WHEN the Dashboard starts, THE Dashboard SHALL establish a connection to the PostgreSQL Database at host 103.253.20.30:29990
2. THE Dashboard SHALL authenticate using the configured database credentials (user: postgres, database: financial-reporting-database)
3. WHEN a connection failure occurs, THE Dashboard SHALL log the error and display a user-friendly error message
4. THE Dashboard SHALL query data from tables balance_sheet_raw, income_statement_raw, and cash_flow_statement_raw
5. THE Dashboard SHALL parse JSONB data from the json_raw column into structured financial indicators

### Requirement 2: Stock Symbol Selection

**User Story:** As a financial analyst, I want to select a specific company by stock symbol, so that I can view that company's financial reports.

#### Acceptance Criteria

1. THE Dashboard SHALL display a dropdown or input field for Stock Symbol selection
2. THE Dashboard SHALL retrieve available Stock Symbols from the PostgreSQL Database
3. WHEN a user selects a Stock Symbol, THE Dashboard SHALL load financial data for that company
4. THE Dashboard SHALL display a default Stock Symbol on initial load
5. WHEN no data exists for a selected Stock Symbol, THE Dashboard SHALL display a message indicating no data is available

### Requirement 3: Time Period Selection and Display

**User Story:** As a financial analyst, I want to view financial data across multiple quarters, so that I can analyze trends over time.

#### Acceptance Criteria

1. THE Dashboard SHALL display financial data for at least 5 consecutive time periods (quarters or years)
2. THE Dashboard SHALL provide a dropdown to switch between quarterly and yearly views
3. WHEN quarterly view is selected, THE Dashboard SHALL display data in columns labeled "Q1 YYYY", "Q2 YYYY", etc.
4. THE Dashboard SHALL automatically determine the most recent available quarters from the PostgreSQL Database
5. THE Dashboard SHALL sort time period columns in chronological order from left to right

### Requirement 4: Financial Statement Tab Navigation

**User Story:** As a financial analyst, I want to switch between different financial statement types, so that I can view Balance Sheet, Income Statement, or Cash Flow data.

#### Acceptance Criteria

1. THE Dashboard SHALL display tabs for "Cân đối kế toán" (Balance Sheet), "Kết quả kinh doanh" (Income Statement), and "LCTT" (Cash Flow Statement)
2. WHEN a user clicks a financial statement tab, THE Dashboard SHALL load and display data from the corresponding database table
3. THE Dashboard SHALL visually highlight the currently active tab with a border or background color
4. THE Dashboard SHALL preserve the selected Stock Symbol and time period when switching between tabs
5. WHEN switching tabs, THE Dashboard SHALL display a loading indicator while fetching data

### Requirement 5: Hierarchical Financial Indicator Display

**User Story:** As a financial analyst, I want to see financial indicators organized in a parent-child hierarchy, so that I can understand the structure and relationships between line items.

#### Acceptance Criteria

1. THE Dashboard SHALL parse nested JSON structures from the json_raw field to determine Indicator hierarchy
2. THE Dashboard SHALL display parent Indicators in bold text
3. THE Dashboard SHALL display child Indicators with visual indentation (e.g., "- " prefix or left padding)
4. THE Dashboard SHALL extract the ten_chi_tieu field from JSON as the display name for each Indicator
5. THE Dashboard SHALL display an icon (bar chart or line chart) next to each Indicator based on its Hierarchy Level

### Requirement 6: Financial Data Value Display

**User Story:** As a financial analyst, I want to see numerical financial values in a readable format, so that I can quickly understand the magnitude of figures.

#### Acceptance Criteria

1. THE Dashboard SHALL extract the so_cuoi_nam field from JSON as the numerical value for each Indicator
2. THE Dashboard SHALL apply the selected Display Unit divisor (1, 1,000, or 1,000,000) to all displayed values
3. THE Dashboard SHALL format numbers with thousand separators (e.g., 1,097.849)
4. WHEN a value is null or missing, THE Dashboard SHALL display "-" in the corresponding cell
5. WHEN a value is negative, THE Dashboard SHALL display the number in red color or with parentheses

### Requirement 7: Display Unit Configuration

**User Story:** As a financial analyst, I want to change the display unit for financial figures, so that I can view data in different scales (units, thousands, millions).

#### Acceptance Criteria

1. THE Dashboard SHALL provide a dropdown with options "1", "1,000", and "1,000,000"
2. WHEN a user selects a Display Unit, THE Dashboard SHALL recalculate and update all displayed values
3. THE Dashboard SHALL divide all so_cuoi_nam values by the selected Display Unit
4. THE Dashboard SHALL update the display without requiring a page reload
5. THE Dashboard SHALL default to "1,000,000" as the initial Display Unit

### Requirement 8: Responsive Table Layout

**User Story:** As a user, I want the financial data table to be readable on different screen sizes, so that I can access the Dashboard from various devices.

#### Acceptance Criteria

1. THE Dashboard SHALL display financial data in an HTML table with fixed headers
2. THE Dashboard SHALL enable horizontal scrolling when the table width exceeds the viewport width
3. THE Dashboard SHALL keep the Indicator name column visible while scrolling horizontally
4. THE Dashboard SHALL adjust font sizes and padding for mobile devices (screen width < 768px)
5. THE Dashboard SHALL maintain table readability with a minimum column width of 100px

### Requirement 9: API Endpoint Integration

**User Story:** As a frontend developer, I want to fetch financial data through RESTful API endpoints, so that the Dashboard can retrieve data dynamically.

#### Acceptance Criteria

1. THE API Backend SHALL provide an endpoint GET /api/income-statements with query parameters stock, year, quarter, and limit
2. THE API Backend SHALL provide an endpoint GET /api/balance-sheets with the same query parameters
3. THE API Backend SHALL provide an endpoint GET /api/cash-flows with the same query parameters
4. THE API Backend SHALL return JSON responses with status code 200 for successful requests
5. WHEN an API request fails, THE API Backend SHALL return an appropriate HTTP error code (400, 404, 500) with an error message

### Requirement 10: Error Handling and User Feedback

**User Story:** As a user, I want to see clear error messages when something goes wrong, so that I understand what happened and can take appropriate action.

#### Acceptance Criteria

1. WHEN the PostgreSQL Database is unreachable, THE Dashboard SHALL display "Unable to connect to database. Please try again later."
2. WHEN no data exists for the selected filters, THE Dashboard SHALL display "No financial data available for the selected criteria."
3. WHEN an API request times out (>30 seconds), THE Dashboard SHALL display "Request timed out. Please refresh the page."
4. THE Dashboard SHALL log all errors to the browser console for debugging purposes
5. THE Dashboard SHALL provide a "Retry" button when recoverable errors occur
