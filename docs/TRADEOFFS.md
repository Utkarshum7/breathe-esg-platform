# Architectural Tradeoffs & Omissions (`TRADEOFFS.md`)

To build a robust, maintainable, and review-friendly Minimum Viable Product (MVP) within the assignment timelines, we made deliberate architectural trade-offs. This document details three major features omitted from the platform and the technical justifications behind these choices.

---

## 1. Omission: No Real-Time WebSockets or SSE for Upload Progress

### What was built instead
We utilize standard HTTP multipart file uploads and leverage Axios's native `onUploadProgress` browser callback to track file upload progress dynamically.

### Why this tradeoff was made
- **High System Complexity**: Implementing real-time Server-Sent Events (SSE) or WebSockets would require integrating Django Channels, setting up an active Redis instance as a channel layer, and managing long-lived asynchronous socket connections.
- **Minimal Workflow Value**: Corporate ESG data files (SAP reports, utility bills, corporate travel logs) are typically under 50MB. Under standard network conditions, HTTP uploads complete in under 5 seconds, making WebSockets an over-engineered addition that introduces potential system failure modes (e.g. connection drops, memory leaks).

---

## 2. Omission: No Multi-Factor Authentication (MFA) or SSO Integration

### What was built instead
We rely on standard Django session authentication and default User model permissions. Analysts are authenticated using DRF’s standard browsable authentication layer.

### Why this tradeoff was made
- **Extraneous Scope**: Setting up enterprise Single Sign-On (SSO) via SAML or OAuth2 requires external identity provider configurations (e.g., Okta, Auth0) and major security configurations.
- **Focus on Core ESG Operations**: An internship assignment evaluates data engineering skills (parsing, normalization, transactions, and audit lock logic). Prioritizing an SSO setup would consume core development time without adding any value to the primary ESG Ingestion Engine or validation rules.

---

## 3. Omission: No Real-time Dynamic PDF OCR Ingestion

### What was built instead
The platform processes data from three structured digital channels: SAP CSV exports, Utility portal CSV tables, and Travel management JSON files.

### Why this tradeoff was made
- **High Dependency & Error Rates**: Running Optical Character Recognition (OCR) on scans of utility bills using external libraries (e.g. Tesseract, PDFPlumber) is highly prone to parsing errors due to varying invoice layout templates. It typically requires expensive machine learning models or third-party paid APIs.
- **Structured Reality**: Standard modern enterprise platforms pull utility bill tables directly from provider portals or energy brokers as digital CSV exports. Focusing on robust structured parsing strategy objects reflects realistic enterprise integration pipelines.
