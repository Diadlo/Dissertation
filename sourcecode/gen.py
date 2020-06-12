def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


def generate_func(handler, result, name, arg_types, arg_names):
    assert(len(arg_types) == len(arg_names))
    args = [ f'{type} {name}' for type, name
            in zip(arg_types, arg_names) ]

    args = ', '.join(args)
    arg_names = ', '.join(arg_names)
    ret = '' if result == 'void' else 'return'
    lines = []
    lines.append(f'typedef {result} (*{name}_f)({args}); ')
    lines.append(f'static {name}_f real_{name} = 0;      ')
    lines.append(f'                                      ')
    lines.append(f'{result} {name}({args})               ')
    lines.append( '{                                     ')
    lines.append(f'  if (!real_{name})                   ')
    lines.append(f'    real_{name} =                     ')
    lines.append(f'      ({name}_f)dlsym(RTLD_NEXT, "{name}"); ')
    lines.append(f'                                      ')
    lines.append(f'  if (initInject())                   ')
    lines.append(f'    {handler}({arg_names});           ')
    lines.append(f'  {ret} real_{name}({arg_names});     ')
    lines.append( '}                                     ')
    return [ line.rstrip() + '\n' for line in lines ]

def parse_gen(line):
    _, handler, result, name, *args_list = line.split()
    types = args_list[::2]
    names = args_list[1::2]
    return (handler, result, name, types, names)

def arg_mangling(arg_type):
    name = ''
    if '*' in arg_type:
        name += 'P'
        arg_type = arg_type.replace('*', '')
    elif '&' in arg_type:
        name += 'R'
        arg_type = arg_type.replace('&', '')

    if 'const' in arg_type:
        name += 'K'
        arg_type = arg_type.replace('const', '').strip()

    assert(not '*' in arg_type)
    assert(not '&' in arg_type)
    assert(not 'const' in arg_type)
    return name + str(len(arg_type)) + arg_type


def str_mangling(s):
    return str(len(s)) + s


def func_mangling(classname, method, args_list):
    args_list = [ arg_mangling(arg) for arg in args_list ]
    args = ''.join(args_list)
    mg_classname = str_mangling(classname)
    mg_method = str_mangling(method)
    if classname == method:
        # Constructor
        return f'_ZN{mg_classname}C1E{args}'
    elif method.startswith('~'):
        # Destructor
        return f'_ZN{mg_classname}D1E{args}'
    else:
        # Normal method
        return f'_ZN{mg_classname}{mg_method}E{args}'


def generate_args_names(types):
    return [ f'a{i}' for i in range(len(types)) ]


def parse_method(line):
    # Remove //method
    line = line.split(None, 1)[1]
    # line == function declaration
    # handler == handler name
    line, handler = tuple(line.split('->'))
    handler = handler.strip()
    # result == return type
    # method_desc == name + args
    result, method_desc = line.split(None, 1)
    result = result.strip()

    method_name, args_str = tuple(method_desc.split('('))
    classname, method = tuple(method_name.split('::'))
    classname = classname.strip()
    method = method.strip()
    # Remove last ')'
    args_str = args_str.strip()[:-1]
    # args_list = [ QString, QWidget ]
    if args_str == '':
        args_list = []
    else:
        args_list = [a.strip() for a in args_str.split(',')]

    return (handler, result, classname, method, args_list)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: {} <input file> <output file>'
                .format(sys.argv[0]))
        sys.exit(1)

    generated = []
    in_name = sys.argv[1]
    out_name = sys.argv[2]
    with open(in_name, 'r') as f:
        for ln in f:
            if ln.startswith('//gen'):
                args = parse_gen(ln)
                generated += generate_func(*args)
            elif ln.startswith('//method'):
                (handler, result, classname, method,
                        arg_types) = parse_method(ln)
                mangled = func_mangling(classname, method,
                        arg_types)
                arg_types = [classname + '*'] + arg_types
                arg_names = generate_args_names(arg_types)
                generated += generate_func(handler, result,
                        mangled, arg_types, arg_names)
            else:
                generated.append(ln)

    with open(out_name, 'w') as f:
        for ln in generated:
            f.write(ln)
