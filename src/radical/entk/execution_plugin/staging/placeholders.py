import radical.utils as ru

logger = ru.get_logger('radical.entk.resolve_placeholder')

def resolve_placeholder_vars(record, cur_pat, cur_iter, cur_stage, cur_task, path):


    # No replacement required -- probably hard-coded paths
    if '$' not in path:
        return path

    logger.debug('Resolving path: %s'%(path))

    # Extract placeholder from path
    if (len(path.split('>')) == 1):
        placeholder = path.split('/')[0]
    else:
        if path.split('>')[0].strip().startswith('$'):
            placeholder = path.split('>')[0].strip().split('/')[0]
        else:
            placeholder = path.split('>')[1].strip().split('/')[0]

    # If placeholder pointing to shared space in sandbox

    if placeholder == "$SHARED":
        return path.replace(placeholder, 'staging://')

    elif len(placeholder.split('_'))==8:
        ref_pat        = int(placeholder.split('_')[1])
        ref_iter    = int(placeholder.split('_')[3])
        ref_stage     = int(placeholder.split('_')[5])

        if placeholder.split('_')[6] == 'TASK':
            ref_task     = int(placeholder.split('_')[7])
            ref_monitor = None
        elif placeholder.split('_')[6] == 'MONITOR':
            ref_task     = None
            ref_monitor = int(placeholder.split('_')[7])


    elif len(placeholder.split('_'))==6:
        ref_pat        = cur_pat
        ref_iter    = int(placeholder.split('_')[1])
        ref_stage     = int(placeholder.split('_')[3])

        if placeholder.split('_')[4] == 'TASK':
            ref_task     = int(placeholder.split('_')[5])
            ref_monitor = None
        elif placeholder.split('_')[4] == 'MONITOR':
            ref_task     = None
            ref_monitor = int(placeholder.split('_')[5])

    elif len(placeholder.split('_'))==4:

        ref_pat        = cur_pat
        ref_iter    = cur_iter
        ref_stage     = int(placeholder.split('_')[1])

        if placeholder.split('_')[2] == 'TASK':
            ref_task    = int(placeholder.split('_')[3])
            ref_monitor = None
        elif placeholder.split('_')[2] == 'MONITOR':
            ref_task     = None
            ref_monitor = int(placeholder.split('_')[3])


    elif len(placeholder.split('_'))==2:

        ref_pat        = cur_pat
        ref_iter    = cur_iter
        ref_stage    = int(placeholder.split('_')[1])
        ref_task    = cur_task

    try:

        logger.debug('Pat: %s, Iter: %s, stage: %s, task: %s, placeholder: %s' \
                        %(ref_pat, ref_iter, ref_stage, ref_task, placeholder))

        if ref_task != None:
            return path.replace(placeholder, record["pat_%s"%(ref_pat)]["iter_%s"%(ref_iter)]["stage_%s"%(ref_stage)]["instance_%s"%(ref_task)]["path"])
        elif ref_monitor != None:
            return path.replace(placeholder, record["pat_%s"%(ref_pat)]["iter_%s"%(ref_iter)]["stage_%s"%(ref_stage)]["monitor_%s"%(ref_task)]["path"])
            
    except Exception, ex:
        print "Please check placeholders used, error: %s"%(ex)