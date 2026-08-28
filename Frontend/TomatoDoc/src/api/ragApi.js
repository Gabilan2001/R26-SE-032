const RAG_BASE_URL = 'https://rag-system-ol4x.onrender.com';
const RAG_TIMEOUT_MS = 90000;

async function fetchWithTimeout(url, options, timeoutMs = RAG_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export async function getTreatmentAdvice(predictedClass) {
  const response = await fetchWithTimeout(`${RAG_BASE_URL}/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ class: predictedClass }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || 'Failed to load advice');
  }

  return data;
}
