export const formatDateTime = (iso) => {
  const dt = new Date(iso);
  return dt.toLocaleString();
};

export const isLowConfidence = (confidence) => Number(confidence) < 70;
