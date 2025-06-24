// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDqHicC9wtcveXprHisjF9IX6lY98JAwkk",
  authDomain: "swiproj.firebaseapp.com",
  projectId: "swiproj",
  storageBucket: "swiproj.firebasestorage.app",
  messagingSenderId: "944992814823",
  appId: "1:944992814823:web:20948cf6f06a6f5e9ac442",
  measurementId: "G-5E0LKZGMEY"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);