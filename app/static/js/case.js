function registerCase() {
  const caseNumber = document.getElementById("caseNumber").value;
  const caseType = document.getElementById("caseType").value;
  const complexity = document.getElementById("complexity").value;
  const judgeExp = document.getElementById("judgeExperience").value;

  fetch(`${API_BASE}/register-case`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      
      "X-Token": localStorage.getItem("token") || "",
    },
    body: JSON.stringify({
      caseNumber: caseNumber,
      caseType: caseType,
      complexity: parseInt(complexity),
      judge_experience: parseInt(judgeExp)
    })
  })
  .then(res => res.json())
  .then(data => {
    alert("Case Registered Successfully!");
    predictDuration(complexity, judgeExp);
  })
  .catch(err => {
    alert("Error registering case");
    console.error(err);
  });
}

function predictDuration(complexity, judgeExp) {
  fetch(`${API_BASE}/predict-duration`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "X-Token": localStorage.getItem("token") || ""
    },
    body: JSON.stringify({
      complexity: parseInt(complexity),
      judge_experience: parseInt(judgeExp)
    })
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("prediction").innerText =
      `Predicted Hearing Duration: ${data.predicted_days} days`;
  });
}
