// Firebase browser SDK imports from CDN
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    onAuthStateChanged,
    signOut as firebaseSignOut,
    getAdditionalUserInfo
} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-auth.js";
import {
    getFirestore,
    collection,
    addDoc,
    getDoc,
    getDocs,
    doc,
    serverTimestamp,
    updateDoc
} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-firestore.js";


// Firebase configuration (copied from your code — safe for public client use)
const firebaseConfig = {
    apiKey: "AIzaSyBRt3kjPXZYiKBcMLgiPSgp6k5IYNM_d2k",
    authDomain: "cite-checker.firebaseapp.com",
    projectId: "cite-checker",
    storageBucket: "cite-checker.firebasestorage.app",
    messagingSenderId: "838498610278",
    appId: "1:838498610278:web:a189efc419c9652a2051a7",
    measurementId: "G-SPQXFNZC3P"
};

// Initialize Firebase services
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const db = getFirestore(app);

// -------------------- Auth Functions -------------------- //
export function signInWithGoogle() {
    return signInWithPopup(auth, provider)
        .then(result => {
            const isNewUser = result._tokenResponse?.isNewUser || false;
            if (isNewUser) {
                throw new Error("Account not found. Please use 'Sign Up' to create a new account.");
            }
            return { user: result.user, credential: GoogleAuthProvider.credentialFromResult(result) };
        });
}

export function signUpWithGoogle() {
    return signInWithPopup(auth, provider)
        .then(async result => {
            const info = getAdditionalUserInfo(result);
            const isNewUser = info?.isNewUser;
            if (!isNewUser) {
                throw new Error("Account already exists. Please use 'Sign In'.");
            }
            await addUserToDatabase(result.user);
            return { user: result.user, credential: GoogleAuthProvider.credentialFromResult(result), isNewUser: true };
        });
}

export function getCurrentUser() {
    return auth.currentUser;
}

export function waitForAuth() {
    return new Promise((resolve, reject) => {
        const unsubscribe = onAuthStateChanged(auth, user => {
            unsubscribe();
            resolve(user);
        }, reject);
    });
}

export function signOut() {
    return firebaseSignOut(auth);
}

// -------------------- Database Functions -------------------- //
export async function addUserToDatabase(user) {
    const usersRef = collection(db, "users");
    return await addDoc(usersRef, {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName
    });
}

export async function addSpeechToDatabase(speechData) {
    const speechRef = collection(db, "speeches");
    const docRef = await addDoc(speechRef, {
        speechId: speechData.speechId,
        listenerId: speechData.listenerId,
        speakerId: speechData.speakerId,
        status: speechData.status || "pending",
        factchecked: speechData.factchecked || "pending",
        timestamp: serverTimestamp(),
        verifiedTime: speechData.verifiedTime || null,
        claims: speechData.claims
    });
    return docRef;
}

export async function getAllUsers() {
    const usersRef = collection(db, "users");
    const querySnapshot = await getDocs(usersRef);
    return querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
    }));
}

export async function getPendingSpeechesForSpeaker(speakerId) {
    const speechesRef = collection(db, "speeches");
    const querySnapshot = await getDocs(speechesRef);
    const pendingSpeeches = [];

    querySnapshot.forEach(doc => {
        const data = doc.data();
        if (data.status === "pending" && data.speakerId === speakerId) {
            pendingSpeeches.push({ id: doc.id, ...data });
        }
    });

    return pendingSpeeches;
}

export async function getAllSpeechesForSpeaker(speakerId) {
    const speechesRef = collection(db, "speeches");
    const querySnapshot = await getDocs(speechesRef);
    return querySnapshot.docs
        .map(docSnap => ({ id: docSnap.id, ...docSnap.data() }))
        .filter(speech => speech.speakerId === speakerId);
}

export async function getSpeech(id) {
    const docRef = doc(db, "speeches", id);
    const docSnap = await getDoc(docRef);
    if (!docSnap.exists()) throw new Error("Speech not found");
    return { id: docSnap.id, ...docSnap.data() };
}

export async function updateSpeechVerification(id, claims) {
    const docRef = doc(db, "speeches", id);
    await updateDoc(docRef, { claims, status: "verified" });
}