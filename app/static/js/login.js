function login(event) {
  if (event) event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {

      
      localStorage.setItem("role", data.role);
      if (data.token) localStorage.setItem("token", data.token);

      alert("Login successful – role: " + data.role);
      if (data.role === "admin" || data.role === "judge") {
        window.location.href = "/dashboard";
      } else {
        window.location.href = "/case-registration";
      }

    } else {
      alert("Invalid credentials");
    }
  })
  .catch(err => console.error(err));
}
