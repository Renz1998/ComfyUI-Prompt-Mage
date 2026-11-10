"""Host-side tolerance policy. Scores are model judgments, not confidence estimates."""
POLICIES={'Relaxed':(65,35,55),'Balanced':(75,50,65),'Strict':(90,75,80)}


def assessment(review,criteria,tolerance='Balanced',physical_tolerance=None,passing_score=None):
    threshold,minimum,quality=POLICIES[tolerance]
    checks=review['checks']
    scores=[min(c.get('score',{'pass':100,'fail':20,'partial':70,'uncertain':50}.get(c['status'],50)),49 if c['status']=='fail' else 85 if c['status']=='partial' else 59 if c['status']!='pass' else 100) for c in checks]
    match=round(sum(scores)/len(scores))
    reasons=[]
    if match<threshold:reasons.append(f'Prompt match {match}/100 is below {threshold}.')
    if min(scores)<minimum:reasons.append('An individual detail is too far from the approved shot.')
    if review.get('quality_score',75)<quality:reasons.append(f'Image usability is below {quality}/100.')
    if review.get('major_defect',False):reasons.append('The reviewer identified a major visible defect.')
    floors={'Relaxed':(70,70,60,60),'Balanced':(85,85,80,80),'Strict':(90,90,85,85)}[physical_tolerance or tolerance]
    integrity=review.get('visual_integrity',{});physical_issues=[]
    for (key,label),floor in zip((('anatomy','Anatomy'),('spatial','Scene geometry'),('clothing','Clothing/materials'),('lighting','Lighting/perspective')),floors):
        item=integrity.get(key)
        if not item or not item.get('applicable',True):continue
        score=min(item['score'],49 if item['status']=='fail' else 59 if item['status']=='uncertain' else 85 if item['status']=='partial' else 100)
        if item['severity']=='major' or score<floor:physical_issues.append(label+': '+item['evidence'])
    reasons.extend(physical_issues)
    for index,c in enumerate(criteria):
        if c.lstrip().startswith('!') and (checks[index]['status']!='pass' or scores[index]<70):reasons.append('A must-have check is missing or uncertain: '+c.lstrip('! '))
    overall=None
    if passing_score is not None:
        if isinstance(passing_score,bool) or not isinstance(passing_score,int) or not 50<=passing_score<=100:raise ValueError('Passing score must be 50–100.')
        physical=[];hard=[]
        floors={'Relaxed':(50,50,50,50),'Balanced':(60,60,60,60),'Strict':(85,85,80,80)}[physical_tolerance or 'Balanced']
        for (key,label),floor in zip((('anatomy','Anatomy'),('spatial','Scene cohesion'),('clothing','Clothing/materials'),('lighting','Image cohesion')),floors):
            item=integrity.get(key)
            if not item or not item.get('applicable',True):continue
            score=min(item['score'],49 if item['status']=='fail' else 59 if item['status']=='uncertain' else 85 if item['status']=='partial' else 100)
            physical.append(score)
            if item['severity']=='major' or item['status']=='fail' or score<floor:hard.append(label+': '+item['evidence'])
        physical_score=sum(physical)/len(physical) if physical else review.get('quality_score',75)
        overall=round(match*.4+review.get('quality_score',75)*.25+physical_score*.35)
        reasons=list(hard);physical_issues=list(hard)
        if review.get('major_defect',False):reasons.append('Major visible defect: cannot auto-accept.')
        for index,c in enumerate(criteria):
            if c.lstrip().startswith('!') and (checks[index]['status']!='pass' or scores[index]<70):reasons.append('A must-have is missing or uncertain: '+c.lstrip('! '))
        if overall<passing_score:reasons.append(f'Overall score {overall}/100 is below the passing score {passing_score}.')
    return dict(overall_score=overall,passing_score=passing_score,match_score=match,threshold=threshold,tolerance=tolerance,acceptable=not reasons,
                physical_tolerance=physical_tolerance or tolerance,integrity_passed=not physical_issues if integrity else None,physical_issues=physical_issues,decision_reason=' '.join(reasons) if reasons else (f'Passed: {overall}/100 overall meets {passing_score}; no blocking defects.' if passing_score is not None else 'Within the selected tolerance; minor differences are allowed.'))
