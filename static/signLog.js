async function initAuthModal() {
  if (document.getElementById("signInDialog")) return;

  const res = await fetch("/static/signLog.html"); 
  const html = await res.text();
  document.body.insertAdjacentHTML("beforeend", html);
  await verify();
}


async function verify(){
    let token = localStorage.getItem("token");
    const signinIcon = document.querySelector("#signIcon");
    const logoutIcon = document.querySelector("#logoutIcon");
    if(token == null){
        signinIcon.style.display = "block";
        logoutIcon.style.display = "none";
    }else{
        let response = await fetch("/api/user/auth", {
            method: "GET",
            headers: {"Authorization": `Bearer ${token}`},
        })
        let result = await response.json();
        if(result.data == null){
            signinIcon.style.display = "block";
            logoutIcon.style.display = "none";
        }else{
            signinIcon.style.display = "none";
            logoutIcon.style.display = "block";
        }
    }
}

async function logout(){
    localStorage.removeItem("token");
    location.reload();
    document.querySelector("#signIcon").style.display = "block";
    document.querySelector("#logoutIcon").style.display = "none";
}

async function openSignDialog() {
    const signInDialog = document.querySelector("#signInDialog");
    const sign_in_block = document.querySelector("#sign_in_block");
    const sign_in_cont = document.querySelector("#sign_in_cont");
    signInDialog.showModal();
    const signInMsg = document.querySelector("#signInMsg");
    signInMsg.style.display = "none";
}

async function orderSchedule(){
    const token = localStorage.getItem("token");
    if(token == null){
        const signInDialog = document.querySelector("#signInDialog");
        const sign_in_block = document.querySelector("#sign_in_block");
        const sign_in_cont = document.querySelector("#sign_in_cont");
        signInDialog.showModal();
        const signInMsg = document.querySelector("#signInMsg");
        signInMsg.style.display = "none";
    }else{
        alert("已經登入囉~");
    }
}

function closeSignIn(){
    const signInDialog = document.querySelector("#signInDialog");
    const sign_in_block = document.querySelector("#sign_in_block");
    const sign_in_cont = document.querySelector("#sign_in_cont");
    const signInEmail = document.querySelector("#signInEmail");
    const signInPassword = document.querySelector("#signInPassword");
    signInEmail.value = "";
    signInPassword.value = "";
    signInDialog.close();
    const signInMsg = document.querySelector("#signInMsg");
    signInMsg.style.display = "none";
}

function openRegist(){
    let signInMsg = document.querySelector("#signInMsg");
    const signInDialog = document.querySelector("#signInDialog")
    const sign_in_block = document.querySelector("#sign_in_block")
    const sign_in_cont = document.querySelector("#sign_in_cont")
    const signUpDialog = document.querySelector("#signUpDialog")
    const signUpName = document.querySelector("#signUpName")
    const signUpEmail = document.querySelector("#signUpEmail")
    const signUpPassword = document.querySelector("#signUpPassword")
    signUpName.value = "";
    signUpEmail.value = "";
    signUpPassword.value = "";
    signInMsg.style.display = "none";
    signInDialog.close();
    signUpDialog.showModal();
}

function closeSignUp(){
    const signInDialog = document.querySelector("#signInDialog")
    const sign_in_block = document.querySelector("#sign_in_block")
    const sign_in_cont = document.querySelector("#sign_in_cont")
    const signUpDialog = document.querySelector("#signUpDialog")
    const signUpName = document.querySelector("#signUpName")
    const signUpEmail = document.querySelector("#signUpEmail")
    const signUpPassword = document.querySelector("#signUpPassword")
    const signUpMsg = document.querySelector("#signUpMsg");
    signUpMsg.style.display = "none";
    signUpName.value = "";
    signUpEmail.value = "";
    signUpPassword.value = "";
    signUpDialog.close();
}

function openSignIn(){
    const signInDialog = document.querySelector("#signInDialog")
    const sign_in_block = document.querySelector("#sign_in_block")
    const sign_in_cont = document.querySelector("#sign_in_cont")
    const signUpDialog = document.querySelector("#signUpDialog")
    const signInEmail = document.querySelector("#signInEmail");
    const signInPassword = document.querySelector("#signInPassword");
    signInEmail.value = "";
    signInPassword.value = "";
    signInDialog.showModal();
    signUpDialog.close();
    const signUpMsg = document.querySelector("#signUpMsg");
    signUpMsg.style.display = "none";
}

async function signIn(){
    const email = document.querySelector("#signInEmail").value;
    const password = document.querySelector("#signInPassword").value;
    const signInDialog = document.querySelector("#signInDialog")
    const sign_in_block = document.querySelector("#sign_in_block")
    const sign_in_cont = document.querySelector("#sign_in_cont")
    const signUpDialog = document.querySelector("#signUpDialog")
    if(email == "" || password == ""){
        const signInMsg = document.querySelector("#signInMsg");
        signInMsg.style.display = "block";
        signInMsg.innerText = "請檢查是否有空格";
        signInMsg.style.color = "red";
        return;
    }else{
            let response = await fetch("/api/user/auth", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json" 
            },
            body: JSON.stringify({"email": email, "password": password})
        });
        let result = await response.json();
        if(result.error == true){
            let signInMsg = document.querySelector("#signInMsg");
            signInMsg.style.display = "block";
            signInMsg.innerText = result.message;
            signInMsg.style.color = "red";
        return;
        }else{
            localStorage.setItem("token",result.token);
            const signInDialog = document.querySelector("#signInDialog");
            const signIcon = document.querySelector("#signIcon");
            /*signInDialog.close();*/
            location.reload();
            let signinIcon = document.querySelector("#signIcon");
            let logoutIcon = document.querySelector("#logoutIcon");
            signinIcon.style.display = "none";
            logoutIcon.style.display = "block";
        }
    }
}

async function signUp() {
    const name = document.querySelector("#signUpName").value;
    const email = document.querySelector("#signUpEmail").value;
    const password = document.querySelector("#signUpPassword").value;
    const signInDialog = document.querySelector("#signInDialog")
    const sign_in_block = document.querySelector("#sign_in_block")
    const sign_in_cont = document.querySelector("#sign_in_cont")
    const signUpDialog = document.querySelector("#signUpDialog")
    if (name == "" || email == "" || password == ""){
        const signUpMsg = document.querySelector("#signUpMsg");
        signUpMsg.style.display = "block";
        signUpMsg.innerText = "請檢查是否有空格"
        signUpMsg.style.color = "red";
        return;
    }else{
        let response = await fetch("/api/user", {
            method: "POST",
            headers: {
                "Content-Type": "application/json" 
            },
            body: JSON.stringify({"name": name, "email": email, "password": password})
        });
        
        let result = await response.json();
        if(result.ok == true){
            const signUpMsg = document.querySelector("#signUpMsg");
            signUpMsg.style.display = "block";
            signUpMsg.style.color = "green";
            signUpMsg.innerText = "註冊成功，請登入系統";
        }else{
            const signUpMsg = document.querySelector("#signUpMsg");
            signUpMsg.style.display = "block";
            signUpMsg.style.color = "red";
            signUpMsg.innerText = result.message;
        }
    }
}
