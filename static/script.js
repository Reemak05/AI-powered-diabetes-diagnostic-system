/*const bar=document.getElementById('bar');
const close=document.getElementById('close');
const nav=document.getElementById('navbar');
if(bar){
    bar.addEventListener('click',()=>{
        nav.classList.add('active');}
        )
}
if(close){
    close.addEventListener('click',()=>{
        nav.classList.remove('active');}
        )
    }

//Login
document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();
    let errorMessage = document.getElementById("errorMessage");

    if (username === "" || password === "") {
        errorMessage.style.display = "block";
        errorMessage.innerText = "Please fill in all fields.";
        return;
    }

    // Simulated authentication check
    if (username === "admin@example.com" && password === "admin123") {
        window.location.href = "admin.html"; // Redirect to admin page
    } else {
        window.location.href = "homepage.html"; // Redirect to homepage for regular users
    }
});

//Register
document.getElementById("registerForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();
    let errorMessage = document.getElementById("errorMessage");

    if (username === "" || password === "") {
        errorMessage.style.display = "block";
        errorMessage.innerText = "Please fill in all fields.";
        return;
    }

    // Simulating successful registration
    alert("Registration successful!");
    window.location.href = "index.html"; // Redirect to login page
});*/





// Register
document.getElementById('registerForm')?.addEventListener('submit', async function (e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  const res = await fetch('/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password })
  });

  const msg = await res.text();
  alert(msg);
});

// Login
document.getElementById('loginForm')?.addEventListener('submit', async function (e) {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;

  const res = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const msg = await res.text();

  if (res.ok) {
    // Login successful → redirect to homepage
    window.location.href = 'homepage.html';
  } else {
    // Login failed → show error message
    alert(msg);
  }
});

// Toggle password visibility for both forms
function togglePassword() {
  const passwordInput = document.getElementById('password') || document.getElementById('loginPassword');
  passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
}


//menu
function toggleMenu() {
    const navbar = document.getElementById("navbar");
    navbar.classList.toggle("show");
}

