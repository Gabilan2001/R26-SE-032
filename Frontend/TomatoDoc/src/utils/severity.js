export function computeSeverity(result, mode = 'nutrient') {
  const confidence = Number(result?.confidence || 0);
  const className = result?.class || '';

  let baseRisk = mode === 'fruit' ? 60 : 50;

  if (mode === 'nutrient') {
    if (className === 'Healthy') baseRisk = 8;
    if (className === 'Nitrogen_Potassium') baseRisk = 78;
    if (className === 'Iron_Deficiency') baseRisk = 55;
  } else {
    if (className === 'Healthy_Tomato') baseRisk = 10;
    if (className === 'Spotted_wilt_Virus') baseRisk = 86;
    if (className === 'Anthracnose') baseRisk = 74;
  }

  const confidenceImpact = Math.round((confidence - 50) * 0.3);
  const score = Math.max(0, Math.min(100, baseRisk + confidenceImpact));

  let level = 'Low';
  if (score >= 70) level = 'High';
  else if (score >= 40) level = 'Medium';

  return { score, level };
}

