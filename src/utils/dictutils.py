
MERGE_FUNCTION_TYPE = 'Callable[[Dict[str, Any], Sequence[str], str], None]'

def getMapOp(operation: 'Callable', dict_obj: 'Dict[str, Any]',
             initial_value: 'Any', *args: str) -> 'Any':

    out = initial_value
    for key in args:
        val = dict_obj.get(key)
        if val is not None:
            operation(out, val)

    return out

def getMapConcat(dict_obj: 'Dict[str, Dict[str, Any]]',
                 *args: str) -> 'Dict[str, Any]':

    return getMapOp(lambda first, second: first.update(second), dict_obj, {},
                    *args)

def getListConcat(dict_obj: 'Dict[str, List[Any]]', *args: str) -> 'List[Any]':

    return getMapOp(lambda first, second: first.extend(second), dict_obj, [],
                    *args)

def mergeBase(
        dict_obj: 'Dict[str, Any]', keys: 'Sequence[str]', target: str,
        function: 'Callable[[Dict[str, Any], List[str]], Dict[str, Any]]') \
            -> None:

    result = function(dict_obj, *keys)
    for key in keys:
        if key in dict_obj:
            del dict_obj[key]

    dict_obj[target] = result

def mergeMap(dict_obj: 'Dict[str, Dict[str, Any]]', keys: 'Sequence[str]',
             target: str) -> None:

    return mergeBase(dict_obj, keys, target, getMapConcat)

def mergeList(dict_obj: 'Dict[str, List[Any]]', keys: 'Sequence[str]',
              target: str) -> None:

    return mergeBase(dict_obj, keys, target, getListConcat)

def merge(dict_obj: 'Dict[str, Any]', keys: 'Sequence[str]', target: str):

    if keys:
        sample_val = next((val for val in (dict_obj.get(key) for key in keys)
                           if val is not None), None)
        if isinstance(sample_val, dict):
            mergeMap(dict_obj, keys, target)
        elif isinstance(sample_val, list):
            mergeList(dict_obj, keys, target)

def hasKeys(dict_obj: 'Dict[str, Any]', keys: 'Sequence[str]',
            operation: 'Callable[[Iterable[bool]], bool]' = all) -> bool:

    return operation(key in dict_obj for key in keys)

def pathMatchAbsolute(dict_obj: 'Dict[str, Any]', path: 'Sequence[str]',
                      has_keys: 'Sequence[str]' = None, start: int = 0,
                      has_keys_op: 'Callable[[Iterable[bool]], bool]' = all,
                      path_may_have_list: bool = True) \
                          -> 'Sequence[Dict[str, Any]]':

    if start > len(path):
        return ()

    if start == len(path):
        if has_keys is None or hasKeys(dict_obj, has_keys,
                                       operation=has_keys_op):
            return (dict_obj,)
        return ()

    default_obj = object()
    current_val = dict_obj.get(path[start], default_obj)

    if current_val is default_obj:
        return ()

    start += 1
    if isinstance(current_val, dict):
        return pathMatchAbsolute(current_val, path, has_keys=has_keys,
                                 start=start, has_keys_op=has_keys_op,
                                 path_may_have_list=path_may_have_list)

    if path_may_have_list and isinstance(current_val, list):

        result = ()
        for content in current_val:
            result += pathMatchAbsolute(
                content, path, has_keys=has_keys, has_keys_op=has_keys_op,
                start=start, path_may_have_list=path_may_have_list)

        return result

    return ()

def pathMatch(dict_obj: 'Dict[str, Any]', path: 'Sequence[str]',
              has_keys: 'Sequence[str]' = None, start: int = 0,
              absolute: bool = False, path_may_have_list: bool = True,
              has_keys_op: 'Callable[[Iterable[bool]], bool]' = all) \
                  -> 'Sequence[Dict[str, Any]]':
    # TODO: Implement function for no absolute path

    if absolute is True:
        return pathMatchAbsolute(dict_obj, path, has_keys=has_keys,
                                 path_may_have_list=path_may_have_list,
                                 start=start, has_keys_op=has_keys_op)

    raise NotImplementedError

def mergeMatch(dict_obj: 'Dict[str, Any]', path: 'Sequence[str]',
               keys: 'Sequence[str]', target: str,
               merge_function: MERGE_FUNCTION_TYPE = merge, **kwargs) -> None:

    if 'has_keys' not in kwargs:
        kwargs['has_keys'] = tuple(key for key in keys if key != target)

    if 'has_keys_op' not in kwargs:
        kwargs['has_keys_op'] = any

    matches = pathMatch(dict_obj, path, **kwargs)

    for match_val in reversed(matches):
        merge_function(match_val, keys, target)
