## ⭐ AutoDev IQ - Frontend

Built on **Next.js**, leveraging **Material UI**, **Framer Motion**, **React Icons**, and **Mermaid.js** for a sleek, interactive, and visually rich user experience.

---

## 📂 Project Structure

```
project-root/
├── public/                      # Static assets

├── src/
│ ├── app/                       # Next.js routes & layouts
│ │ ├── about/                   # About page
│ │ ├── login/                   # Login page
│ │ ├── register/                # Registration page
│ │ ├── semantic-search/         # Semantic search route
│ │ │ ├── layout.js
│ │ │ └── page.js
│ │ ├── layout.js                # Root layout
│ │ └── page.js                  # Home page

│ ├── components/                # Reusable UI components
│ ├── context/                   # Each Page React context
│ ├── reusables/                 # Shared smaller components
│ └── utils/                     # Helper functions

├── .env.local
├── Dockerfile                   # Docker file to run frontend folder
└── package.json
```

---

## 🌐 Project Routes

| Route                | Description                         |
| -------------------- | ----------------------------------- |
| `/`                  | Home page                           |
| `/about`             | About the project                   |
| `/login`             | User login page                     |
| `/register`          | User registration page              |
| `/semantic-search`   | Semantic code search UI             |
| `/test-generation`   | Test generation interface           |
| `/visual-regression` | Visual regression testing dashboard |

---

## 🚀 Getting Started

### **1. Prerequisites**
Make sure you have installed:
- [Node.js](https://nodejs.org/) (v18 or above recommended)
- npm or yarn (npm comes with Node.js)


### **2. Installation**
```bash
npm install  # To Download all dependencies
```


### **3. Running the Application**

To run development server:

```bash
npm run dev
```

To run build:

```bash
npm run build
npm run start
```

## 🧑‍💻 Setting Up .env.local

Our application’s folder structure data is fetched directly from **GitHub’s REST API**.  
By default, **unauthenticated** requests to GitHub’s API have a rate limit of **60 calls/hour per IP address**.  
This can quickly become a blocker when:
- Browsing multiple folders
- Refreshing frequently
- Switching between projects (repeated API calls)

To mitigate this, we use a **GitHub Personal Access Token (PAT)**, which raises the limit to **5,000 calls/hour per IP**.


### 🔑 Steps to Generate & Add Your GitHub Token

1. **Go to GitHub Settings**  
   Navigate to [GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens).

2. **Generate New Token**  
   - Click **"Generate new token" → "Generate new token (classic)"**  
   - Add a note (e.g., `AutoDev IQ Frontend`)  
   - Set expiration as per your preference  
   - **Scopes:** No scopes are required for public repositories (keep all unchecked).

3. **Copy the Token**  
   Once generated, **copy** your token. You won’t be able to see it again later.

4. **Create `.env.local` File** (if not present)  
   In the **project root**, create a `.env.local` file.

5. **Add Your Token to `.env.local`**  
   ```env
   NEXT_PUBLIC_GITHUB_TOKEN=yourTokenHere
   ```