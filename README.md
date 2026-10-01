# IS6153-StudySync

what is StudySync?
StudySync is a client-side mobile web application. For rapid prototyping and demonstration, the entire application runs in the browser. All user data is stored locally using localStorage, eliminating the need for a backend server. This allows for fast deployment and simplifies the development and demo process. For the final production version, the architecture will transition to a full-stack model. All user data will be persisted securely in a remote database, moving away from local browser storage. An optional smart recommendation feature for Premium-tier users is powered by the Anthropic API (Claude). The API calls are made directly from the client to generate personalized insights.

# screenshot
<img width="968" height="1618" alt="image" src="https://github.com/user-attachments/assets/60f73999-3aec-4520-84a3-bccef3d209dd" />
<img width="916" height="1375" alt="image" src="https://github.com/user-attachments/assets/f07566c0-792c-4580-a629-bbf9773babca" /> # add task
<img width="925" height="1580" alt="image" src="https://github.com/user-attachments/assets/de7c6618-31fb-467a-9a00-c9d675df200d" />
<img width="938" height="1620" alt="image" src="https://github.com/user-attachments/assets/afbf7784-eda0-455e-af95-11928d7ca93f" />
<img width="955" height="1613" alt="image" src="https://github.com/user-attachments/assets/0f003e10-c11a-48dd-bba7-3215725cb66a" />
<img width="981" height="1608" alt="image" src="https://github.com/user-attachments/assets/25f364d0-e2e4-415c-8fee-cd378b5f1a37" />

# The system follows a three-layer client-centric architecture:
Layer	Technology	Responsibility
Presentation Layer	HTML / CSS / JavaScript 	Renders all UI screens, handles user interactions, navigation between pages
Application Logic Layer	Python	Processes data, enforces business rules, manages state, calls external APIs
Data Layer	Browser localStorage	Persists user profile, tasks, study logs, settings, and notification preferences




