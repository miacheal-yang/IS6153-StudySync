# 🌟 IS6153 — StudySync

## 📱 Overview
**StudySync is a lightweight, client-side mobile web application designed for rapid prototyping and demonstration.**  
The entire system runs fully in the browser, with all user data stored locally via `localStorage`  [Current page](citation-section://1421309710/5).  
This architecture enables:

- Zero backend dependencies  
- Instant deployment  
- Simplified demo and testing workflows  

A future production version will transition to a **full-stack architecture**, where user data is securely persisted in a remote database instead of browser storage  [Current page](citation-section://1421309710/8).

Premium-tier users can access an optional **AI-powered smart recommendation feature**, implemented using the **Anthropic Claude API**, called directly from the client to generate personalized insights  [Current page](citation-section://1421309710/9).

---

# 🚀 Key Features

### **1. Fully Client-Side Execution**
- Runs entirely in the browser  
- No backend server required  
- Data stored using `localStorage`  
- Ideal for rapid prototyping and classroom demos  

### **2. AI-Powered Study Recommendations (Premium)**
- Integrates **Anthropic Claude API**  
- Generates personalized study insights based on tasks and logs  
- API requests made directly from the client  

### **3. Production-Ready Architecture Roadmap**
- Planned migration to a full-stack model  
- Secure remote database storage  
- Scalable backend integration  

---

# 🧱 High-Level Architecture

StudySync follows a **three-layer client-centric architecture**  [Current page](citation-section://1421309710/20):

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| **Presentation Layer** | HTML / CSS / JavaScript | UI rendering, user interaction, page navigation |
| **Application Logic Layer** | Python | Data processing, business rules, state management, external API calls |
| **Data Layer** | Browser `localStorage` | Persists user profile, tasks, study logs, settings, notification preferences |

---

## 🔌 External Integrations

| Service | Purpose | Tier |
|---------|---------|------|
| **Anthropic API (Claude)** | Personalized study recommendations | Premium |
| **Browser Notification API** | In-app reminders for deadlines | Free & Premium |
| **File Save API** | Export study data (CSV / PDF) | Premium |

---

# 🧩 Architectural Style

StudySync adopts a **Component-Based Architecture**, where the UI is composed of modular, reusable components such as:

- `TaskCard`  
- `LogEntry`  
- `SummaryWidget`  
- `NotificationBanner`  
- `StatCard`

### Benefits
- **Separation of concerns** — each component manages its own display logic  
- **Reusability** — shared components across multiple pages  
- **Maintainability** — components can be updated or tested independently  
- **Scalability** — backend integration can be added without redesigning the UI layer  

### State Management
A lightweight centralized store (JavaScript object) synchronizes with `localStorage`, ensuring persistence across browser sessions.

---

# 📸 Screenshots

### **Main Interface**
```html
<p align="center">
  <img src="https://raw.githubusercontent.com/miacheal-yang/IS6153-StudySync/refs/heads/main/images/home.png" width="45%">
</p>
```

### **Task Management Flow**
```html
<p align="center">
  ![StudySync Log Screen](https://raw.githubusercontent.com/miacheal-yang/IS6153-StudySync/main/images/log.png)
</p>
```

### **Profile**
```html
<p align="center">
  <img src="https://raw.githubusercontent.com/miacheal-yang/IS6153-StudySync/blob/main/images/profile.png" width="40%">
</p>
```
---

# 🛠 Tech Stack

- **Frontend:** HTML / CSS / JavaScript  
- **Logic:** Python  
- **Storage:** Browser `localStorage`  
- **AI:** Anthropic Claude API  
- **Deployment:** GitHub Pages  

---

# 📦 Getting Started

### **1. Clone the Repository**
```bash
git clone https://github.com/miacheal-yang/IS6153-StudySync.git
```

---

# 🧪 AI Recommendation Example (Claude API)

```python
def get_recommendation(user_profile):
    payload = {
        "model": "claude-3-sonnet",
        "prompt": f"Generate study advice for: {user_profile}"
    }
    return requests.post(API_URL, json=payload).json()
```

---

# 🎯 Project Goals

- Deliver a functional mobile learning prototype  
- Demonstrate front-end architecture skills  
- Showcase AI API integration  
- Provide a foundation for future full-stack expansion  

---

# 👤 Author

**Peng Yang — University College Cork (MSc Information Systems for Business Performance)**  
Focus areas: Python, BI, Systems Analysis, AI Application Development, Mobile Prototyping.
