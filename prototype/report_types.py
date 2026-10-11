"""Meeting-specific framing. All reports remain internal BD preparation briefs."""
REPORT_TYPES={
    'Engineering': {'focus':'Reliability, technical blockers, investigation updates and delivery uncertainties.',
                    'prompt':'Lead with engineering investigations and technical blockers, then relevant partner evidence and dependencies. Focus on platform reliability and unresolved delivery questions.'},
    'Vendor': {'focus':'Infrastructure performance, proposed maintenance, dependencies and questions for the vendor.',
               'prompt':'Lead with vendor updates and proposed maintenance. Include infrastructure reliability, operational dependencies and vendor discussion questions. Omit onboarding or product-feature feedback unless the sources explicitly connect it to a vendor dependency. Separate proposals from approved changes. If vendor-specific evidence is absent, say it is absent rather than inventing vendor updates. Prefer fewer relevant findings to filling the suggested finding count with unrelated material.'},
    'Partner': {'focus':'Adoption, onboarding, partner feedback and questions for the next partner conversation.',
                'prompt':'Lead with partner feedback, adoption context, onboarding and unresolved expectations. Include technical updates only when they help BD discuss those needs. Do not invent commercial outcomes or treat an engineering investigation as a promised fix. Preserve the identity of the partner that supplied each claim; never attribute one partner feedback to another.'},
}


def for_report_type(sources_bytes,report_type):
    import json
    if report_type not in REPORT_TYPES: raise ValueError('Choose Engineering, Vendor or Partner.')
    data=json.loads(sources_bytes)
    data['report_type']=report_type
    return json.dumps(data,ensure_ascii=False).encode()
