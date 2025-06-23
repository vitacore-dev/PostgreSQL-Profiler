// Полифилл для crypto.randomUUID для совместимости со старыми браузерами и Node.js
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Для браузерного окружения
if (typeof window !== 'undefined') {
  if (!window.crypto) {
    window.crypto = {};
  }
  
  if (!window.crypto.randomUUID) {
    window.crypto.randomUUID = generateUUID;
  }
}

// Для Node.js окружения
if (typeof globalThis !== 'undefined' && typeof globalThis.global !== 'undefined') {
  if (!globalThis.global.crypto) {
    globalThis.global.crypto = {};
  }
  
  if (!globalThis.global.crypto.randomUUID) {
    globalThis.global.crypto.randomUUID = generateUUID;
  }
}

// Для модульного окружения
if (typeof globalThis !== 'undefined') {
  if (!globalThis.crypto) {
    globalThis.crypto = {};
  }
  
  if (!globalThis.crypto.randomUUID) {
    globalThis.crypto.randomUUID = generateUUID;
  }
}

export default {};

