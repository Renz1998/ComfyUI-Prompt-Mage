"""Host-side tolerance policy. Scores are model judgments, not confidence estimates."""
POLICIES={'Relaxed':(65,35,55),'Balanced':(75,50,65),'Strict':(90,75,80)}


def assessment(review,criteria,tolerance='Balanced'):
    threshold,minimum,quality=POLICIES[tolerance]
    checks=review['checks']
    scores=[min(c.get('score',{'pass':100,'fail':20,'uncertain':50}[c['status']]),49 if c['status']=='fail' else 59 if c['status']=='uncertain' else 100) for c in checks]
    match=round(sum(scores)/len(scores))
    reasons=[]
    if match<threshold:reasons.append(f'Prompt match {match}/100 is below {threshold}.')
    if min(scores)<minimum:reasons.append('An individual detail is too far from the approved shot.')
    if review.get('quality_score',75)<quality:reasons.append(f'Image usability is below {quality}/100.')
    if review.get('major_defect',False):reasons.append('The reviewer identified a major visible defect.')
    for index,c in enumerate(criteria):
        if c.lstrip().startswith('!') and (checks[index]['status']!='pass' or scores[index]<70):reasons.append('A must-have check is missing or uncertain: '+c.lstrip('! '))
    return dict(match_score=match,threshold=threshold,tolerance=tolerance,acceptable=not reasons,
                decision_reason=' '.join(reasons) if reasons else 'Within the selected tolerance; minor differences are allowed.')
