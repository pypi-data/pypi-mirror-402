
def reader_init(reader_type, available_args):
    """initialise reader object

    Readers usually need some information not shared by other readers
    For example, some readers search many files for a valid entries while others
    will need instruction to build specific filenames.

    Moreover, the same reader can be used irrespective of the fact that a quantity
    is considered a 'reference' or the 'verified' quantity.
    Consider how radar data can be a reference when verifying model forecast while it may also be verified 
    against other precipitation products. 

    In the call to gridded_obs, by convention:
        - all variables specific to the 'reference' reader will have the 'reference_' prefix
        - all variables specific to the 'verified'  reader will have the 'verified_'  prefix

    In this function, a reader object is created by:
        - make a dictionary containing all the 'reference' or 'verified' arguments from args object
        - the 'reference_' or 'verified_' prefix are removed so that readers can be used in either cases

    args:
        reader_type:    [str] either 'reference' or 'verified'
        available_args: [object] the "unknown_args" produced by parsing arguments in gridded_obs
                                 contains both the 'reference_' and 'verified_' arguments

    returns:
        A reader object 
    
    """

    import gridded_obs.readers as readers

    if not ((reader_type == 'reference') or (reader_type == 'verified')):
        raise ValueError('reader_type may only be only "reference" or "verified"')

    #add underscore to reader type
    reader_type += '_'

    #make list of arguments for reference or verified function 
    #prefix is removed, and variables not related to 'reader_type' are discarted
    #
    #for example with reader_type='verified' ; 
    #   ['--verified_pr_dt', '10', '--reference_data_dir', '/path/to/data/dir']
    #becomes
    #   {'pr_dt':'10'}

    #the following assumes only one key-value pair 
    #situation such as ['--verified_argument', '10', '20', '30'] will not be handled correctly
    arg_dict = {}
    for ii, element in enumerate(available_args):
        if element.startswith('--'+reader_type):
            #element is an argument of desired type
            #save argument with prefix removed
            key = element[len(reader_type)+2:]
            value = available_args[ii+1]
            arg_dict[key] = value

    #get reader function
    this_reader = getattr(readers, arg_dict['reader'])

    #remove reader from argument dict
    del arg_dict['reader']

    return this_reader(**arg_dict)







