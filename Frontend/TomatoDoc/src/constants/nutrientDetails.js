export const nutrientDetails = {
  Healthy: {
    title: 'Healthy Leaf',
    visualSymptoms: 'Leaf shows uniform green color with no visible chlorosis or necrosis.',
    treatment: ['Continue current irrigation schedule.', 'Maintain balanced fertilization.', 'Inspect plants weekly for early signs.'],
    dosage: 'No corrective dosage needed.',
  },
  Nitrogen: {
    title: 'Nitrogen Deficiency',
    visualSymptoms: 'Older leaves become pale yellow and plant growth slows down.',
    treatment: ['Apply nitrogen fertilizer immediately.', 'Split application into two doses.', 'Recheck leaves in 7 days.'],
    dosage: 'Urea (46-0-0): 200 kg/hectare.',
  },
  Potassium: {
    title: 'Potassium Deficiency',
    visualSymptoms: 'Brown or scorched margins with weak stems and reduced fruit quality.',
    treatment: ['Apply potassium sulfate around root zone.', 'Water after application.', 'Monitor edge burn reduction over 10 days.'],
    dosage: 'Potassium Sulfate (0-0-50): 150 kg/hectare.',
  },
  Nitrogen_Potassium: {
    title: 'Nitrogen + Potassium Deficiency',
    visualSymptoms: 'Mixed chlorosis with marginal necrosis and overall weak growth.',
    treatment: ['Apply balanced N-K fertilizer blend.', 'Split into two rounds a week apart.', 'Track new leaf color.'],
    dosage: 'NPK (15-0-15): 250 kg/hectare.',
  },
  Phosphorus: {
    title: 'Phosphorus Deficiency',
    visualSymptoms: 'Dark green foliage with purple tint under leaves and weak root development.',
    treatment: ['Apply phosphorus source to soil.', 'Avoid over-watering after application.', 'Reassess root vigor in 10-14 days.'],
    dosage: 'Superphosphate: 250 kg/hectare.',
  },
  Iron_Deficiency: {
    title: 'Iron Deficiency',
    visualSymptoms: 'Young leaves turn yellow while veins remain green (interveinal chlorosis).',
    treatment: ['Spray iron chelate on foliage.', 'Repeat every 2 weeks.', 'Correct high pH if present.'],
    dosage: 'FeSO4 foliar spray as label recommendation every 14 days.',
  },
};
