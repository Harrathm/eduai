const API_URL = "http://localhost:8000";

async function authAPI_login(email, password) {
  const params = new URLSearchParams();
  params.append("username", email);
  params.append("password", password);
  
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params,
  });
  console.log("Status:", res.status);
  if (!res.ok) throw new Error("Login failed " + res.status);
  return res.json();
}

authAPI_login("admin@eduai.platform", "admin123")
  .then(data => console.log("Success:", data))
  .catch(err => console.error("Error:", err.message));