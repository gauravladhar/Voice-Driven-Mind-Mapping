// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";


const firebaseConfig = {
  apiKey:            "AIzaSyB4F-SLZaQ5LsfwpWGlP530Jv1zMyabK40",
  authDomain:        "mapped-out-93456.firebaseapp.com",
  projectId:         "mapped-out-93456",
  storageBucket:     "mapped-out-93456.appspot.com", // fixed .appspot.com suffix
  messagingSenderId: "908839404892",
  appId:             "1:908839404892:web:43e1b0fb04a70185cb2d99",
  measurementId:     "G-SYN292Y4F0",
};

const app  = initializeApp(firebaseConfig);
export const auth = getAuth(app);
const provider   = new GoogleAuthProvider();

/* helpers ------------------------------------------------------------- */
export async function signIn()  { await signInWithPopup(auth, provider); }
export async function logOut()  { await signOut(auth); }

export function checkAuth() {
  return new Promise((resolve) => {
    const unsub = auth.onAuthStateChanged((user) => {
      unsub();                    // one-shot listener
      resolve(user);              // null if not signed in
    });
  });
}
