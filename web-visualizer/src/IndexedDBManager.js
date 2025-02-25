const dbName = 'AgenticAIDB';
const dbVersion = 1;
const storeName = 'stimuli';

const openDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, dbVersion);

    request.onerror = (event) => reject(event.target.error);

    request.onsuccess = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(storeName)) {
        // If the object store doesn't exist, close the database and reopen it with a new version
        db.close();
        const newRequest = indexedDB.open(dbName, db.version + 1);
        newRequest.onupgradeneeded = createObjectStore;
        newRequest.onsuccess = (event) => resolve(event.target.result);
        newRequest.onerror = (event) => reject(event.target.error);
      } else {
        resolve(db);
      }
    };

    request.onupgradeneeded = createObjectStore;
  });
};

const createObjectStore = (event) => {
  const db = event.target.result;
  if (!db.objectStoreNames.contains(storeName)) {
    db.createObjectStore(storeName, { keyPath: "stimulus_uuid" });
  }
};

export const storeInIndexedDB = async (stimulus) => {
  const db = await openDB();
  const transaction = db.transaction([storeName], "readwrite");
  const store = transaction.objectStore(storeName);
  return new Promise((resolve, reject) => {
    if (!stimulus || !stimulus.stimulus_uuid) {
      console.warn("Invalid stimulus or missing stimulus_uuid", stimulus);
      resolve();
      return;
    }

    // Extract string value if it's a Solace message ID object
    const key = typeof stimulus.stimulus_uuid === 'object' && stimulus.stimulus_uuid._value
      ? stimulus.stimulus_uuid._value
      : stimulus.stimulus_uuid;
    
    if (!key) {
      console.warn("Invalid key for stimulus", stimulus);
      resolve();
      return;
    }

    const getStimulus = store.get(key);
    getStimulus.onerror = () => reject(getStimulus.error);
    getStimulus.onsuccess = () => {
      let stimulusUpdate;
      if (getStimulus.result) {
        // Update existing stimulus
        const updatedStimulus = {
          ...getStimulus.result,
          ...stimulus,
          stimulus_uuid: key, // Ensure we store the string key
          responses: [...(getStimulus.result.responses || []), ...(stimulus.responses || [])]
        };
        stimulusUpdate = store.put(updatedStimulus);
      } else {
        // Add new stimulus with string key
        stimulusUpdate = store.put({
          ...stimulus,
          stimulus_uuid: key // Ensure we store the string key
        });
      }
      stimulusUpdate.onerror = (error) => {
        console.error("Error updating stimulus in IndexedDB", error);
        reject(stimulusUpdate.error);
      };
      stimulusUpdate.onsuccess = () => {
        resolve();
      };
    };
  });
};

export const getFromIndexedDB = async () => {
  const db = await openDB();
  const transaction = db.transaction([storeName], "readonly");
  const store = transaction.objectStore(storeName);
  return new Promise((resolve, reject) => {
    const stimulus = store.getAll();
    stimulus.onerror = () => reject(stimulus.error);
    stimulus.onsuccess = () => {
      const stimuli = {};
      stimulus.result.forEach(stimulus => {
        if (stimulus.stimulus_uuid) {
          stimuli[stimulus.stimulus_uuid] = stimulus;
        }
      });
      resolve(stimuli);
    };
  });
};

export const clearIndexedDB = async () => {
  const db = await openDB();
  const transaction = db.transaction([storeName], "readwrite");
  const store = transaction.objectStore(storeName);
  return new Promise((resolve, reject) => {
    const stimulus = store.clear();
    stimulus.onerror = () => reject(stimulus.error);
    stimulus.onsuccess = () => resolve();
  });
};
