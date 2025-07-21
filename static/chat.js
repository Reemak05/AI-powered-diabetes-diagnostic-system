
document.addEventListener("DOMContentLoaded", () => {
    
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    const userData = {};
    const questions = [
        { key: "age", text: "How old are you?", type: "number" },
        { key: "gender", text: "What is your gender? (male/female)", type: "text" },
        { key: "pregnancy", text: "How many times have you been pregnant?", type: "number", condition: () => userData.gender === "female" },
        { key: "weight", text: "Your weight in kg?", type: "number" },
        { key: "height", text: "Your height in cm?", type: "number" },
        { key: "glucose", text: "Your glucose level?", type: "number" },
        { key: "blood_pressure", text: "Your blood pressure (mm Hg)?", type: "number" },
        { key: "insulin", text: "Your insulin level (mu U/ml)?", type: "number" },
        { key: "parent_diabetes", text: "Do your parents have diabetes? (yes/no)", type: "text" },
        { key: "sibling_diabetes", text: "Do your siblings have diabetes? (yes/no)", type: "text" },
        { key: "predict", text: "Would you like a diabetes prediction? (yes/no)", type: "text" }
    ];

    let currentQuestionIndex = 0;
    let awaitingTypeConfirmation = false;

    const getCurrentDate = () => {
        const date = new Date();
        const day = String(date.getDate()).padStart(2, "0");
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const year = date.getFullYear();
        return `${day}-${month}-${year}`;
    };
    
    const addMessage = (message, isBot = true) => {
        const msg = document.createElement("div");
        msg.className = "chat-message " + (isBot ? "bot-message" : "user-message");
        msg.textContent = message;
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const predictDiabetesType = (insulin, diabetesPedigree, age, bmi, glucose) => {
    if (age < 25 && insulin < 50 && bmi < 20) {
        return "Type 1 Diabetes";
    }

    if (age >= 25 && bmi >= 25 && glucose >= 126) {
        return "Type 2 Diabetes";
    }
    
    if (glucose >= 100 && glucose < 126) {
        return "Prediabetes";
    }

    return "Prediabetes";
}


   

    const askNext = () => {
        while (currentQuestionIndex < questions.length) {
            const q = questions[currentQuestionIndex];
            if (!q.condition || q.condition()) {
                addMessage(q.text);
                break;
            }
            currentQuestionIndex++;
        }
    };

    const validateAnswer = (key, value) => {
        switch (key) {
            case "age":
                if (isNaN(value) || value <= 0 || value > 200)
                    return { isValid: false, message: "Please enter a valid age (1–200)." };
                break;
            case "gender":
                if (!["male", "female"].includes(value.toLowerCase()))
                    return { isValid: false, message: "Gender must be 'male' or 'female'." };
                break;
            case "pregnancy":
                if (isNaN(value) || value < 0 || value > 40)
                    return { isValid: false, message: "Pregnancies must be 0–40." };
                break;
            case "weight":
                if (isNaN(value) || value < 10 || value > 400)
                    return { isValid: false, message: "Weight must be between 10–400 kg." };
                break;
            case "height":
                if (isNaN(value) || value < 50 || value > 300)
                    return { isValid: false, message: "Height must be between 50–300 cm." };
                break;
            case "glucose":
                if (isNaN(value) || value < 40 || value > 500)
                    return { isValid: false, message: "Glucose must be 40–500 mg/dL." };
                break;
            case "blood_pressure":
                if (isNaN(value) || value < 40 || value > 250)
                    return { isValid: false, message: "Blood pressure must be 40–250 mm Hg." };
                break;
            case "insulin":
                if (isNaN(value) || value < 10 || value > 1000)
                    return { isValid: false, message: "Insulin must be 10–1000 mu U/ml." };
                break;
            case "parent_diabetes":
            case "sibling_diabetes":
            case "predict":
                if (!["yes", "no"].includes(value.toLowerCase()))
                    return { isValid: false, message: "Answer must be 'yes' or 'no'." };
                break;
        }
        return { isValid: true };
    };

    const validateUserData = (data) => {
        if (!data.age || !data.gender || !data.weight || !data.height || !data.glucose || !data.blood_pressure || !data.insulin) {
            return { isValid: false, message: "Please complete all fields before prediction." };
        }
        return { isValid: true };
    };









    
    const sendMessage = () => {
        const input = userInput.value.trim();
        if (!input) return;

        if (awaitingTypeConfirmation) {
            addMessage(input, false);
            userInput.value = "";
            if (input.toLowerCase() === "yes") {
                // This block was empty in original code - no action needed here?
                // You can add any follow-up logic if needed.
                addMessage("Thank you for confirming. Stay safe and consult your doctor if needed.");
            } else {
                addMessage("No problem. Stay safe and consult your doctor if you have concerns.");
            }
            awaitingTypeConfirmation = false;
            return;
        }

        addMessage(input, false);
        const q = questions[currentQuestionIndex];
        userInput.value = "";

        const validationResult = validateAnswer(q.key, input);
        if (!validationResult.isValid) {
            addMessage(validationResult.message);
            return;
        }

        userData[q.key] = input.toLowerCase();
        currentQuestionIndex++;

        if (q.key === "predict") {
            if (input.toLowerCase() === "yes") {
                const finalValidation = validateUserData(userData);
                if (!finalValidation.isValid) {
                    addMessage(finalValidation.message);
                    currentQuestionIndex--; // Let user re-answer the same question
                    return;  // No awaitingTypeConfirmation here - user needs to fix missing data
                }

                // Prepare payload for backend prediction
                const payload = {
                    pregnancies: parseInt(userData.pregnancy || 0),
                    glucose: parseFloat(userData.glucose),
                    blood_pressure: parseFloat(userData.blood_pressure),
                    insulin: parseFloat(userData.insulin),
                    bmi: parseFloat((userData.weight / ((userData.height / 100) ** 2)).toFixed(2)),
                    diabetes_pedigree: (userData.parent_diabetes === "yes" || userData.sibling_diabetes === "yes") ? 0.6 : 0.1,
                    age: parseInt(userData.age)
                };

                fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.result === 1) {
                        const bmi = parseFloat((userData.weight / ((userData.height / 100) ** 2)).toFixed(2));
                        const diabetesPedigree = (userData.parent_diabetes === "yes" || userData.sibling_diabetes === "yes") ? 0.6 : 0.1;
                        const diabetesType = predictDiabetesType(
                            parseFloat(userData.insulin),
                            diabetesPedigree,
                            parseInt(userData.age),
                            bmi,
                            parseFloat(userData.glucose)
                        );

                        addMessage("You may be diabetic. Please consult a doctor.");
                        addMessage(`Estimated Diabetes Type: ${diabetesType}`);
                        if (diabetesType === "Type 1 Diabetes") {
                            addMessage("💡 Recommendation: Follow your insulin therapy plan closely, monitor your blood sugar regularly, eat consistent meals, and stay physically active.");
                        } else if (diabetesType === "Type 2 Diabetes") {
                            addMessage("💡 Recommendation: Focus on weight management, adopt a low-sugar balanced diet, stay active, and take medications as prescribed by your doctor.");
                        } else if (diabetesType === "Prediabetes") {
                            addMessage("💡 Recommendation: You can reverse prediabetes! Eat healthier, exercise regularly, lose excess weight, and get regular checkups to stay on track.");
                        }
                    } else if (data.result === 0) {
                        addMessage("You are not diabetic. Stay healthy!");
                    } else {
                        
                        const errorMsg = data.message || "Prediction could not be completed. Please try again later.";
                        addMessage(errorMsg);
                    }
                })
                .catch(() => {
                    addMessage("Error processing your prediction. Please try again.");
                });
            } else if (input.toLowerCase() === "no") {
                // User said no to prediction, do NOT send prediction messages
                addMessage("Okay, no problem. Stay safe and consult your doctor if you have concerns.");
            }
        } else {
            askNext();
        }
    };

    // Send on Enter key
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send on button click
    sendButton.addEventListener("click", sendMessage);

    const dateMessage = getCurrentDate();
    const dateElement = document.querySelector(".date-message");
    dateElement.textContent = ` ${dateMessage}`;
    dateElement.classList.add('date-message-styled');

    // Start the conversation
    askNext();

    // Menu toggling
    const menuDots = document.getElementById("menu-dots");
    const menuOptions = document.getElementById("menu-options");

    menuDots.addEventListener("click", () => {
        menuOptions.classList.toggle("show");
    });

    // Logout handler
    document.getElementById("logout").addEventListener("click", () => {
        if (confirm("Are you sure you want to logout?")) {
            window.location.href = "/logout";
        }
    });

});

document.addEventListener("DOMContentLoaded", () => {
    const darkToggle = document.getElementById("darkToggle");

    // Load saved theme from localStorage
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
        darkToggle.checked = true;
    }

    darkToggle.addEventListener("change", () => {
        document.body.classList.toggle("dark-mode");
        localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
    });
});

function downloadChat() {
  const chatBox = document.getElementById("chat-box");
  const messages = chatBox.querySelectorAll(".chat-message");
  let text = "";

  messages.forEach(msg => {
    text += msg.innerText + "\n";
  });

  const blob = new Blob([text], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "chat_history.txt";
  link.click();
}


