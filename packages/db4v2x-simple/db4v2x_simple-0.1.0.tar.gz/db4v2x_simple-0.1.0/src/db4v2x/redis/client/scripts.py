batch_set_script = """
    local expire = tonumber(ARGV[#ARGV]) 
    local value_count = #ARGV - 1        

    for i = 1, value_count do
        redis.call('SET', KEYS[i], ARGV[i], 'EX', expire)
    end

    return value_count
    """

batch_get_script = """
    local results = {}
    for i, key in ipairs(KEYS) do
        results[i] = redis.call('GET', key)
    end
    return results
    """

batch_hset_script = """
    local num_keys = #KEYS
    local ex = tonumber(ARGV[#ARGV])
    local arg_index = 1

    for i = 1, num_keys do
        local key = KEYS[i]
        local num_fields = tonumber(ARGV[arg_index])
        arg_index = arg_index + 1

        local hset_args = {}
        for j = 1, num_fields do
            hset_args[#hset_args + 1] = ARGV[arg_index]       -- field
            hset_args[#hset_args + 1] = ARGV[arg_index + 1]   -- value
            arg_index = arg_index + 2
        end

        -- HSET key f1 v1 f2 v2 ...
        redis.call("HSET", key, unpack(hset_args))
        redis.call("EXPIRE", key, ex)
    end

    return num_keys
    """


batch_hget_script = """
    local res = {}
    local arg_idx = 1

    for i = 1, #KEYS do
        local key = KEYS[i]
        local n_fields = tonumber(ARGV[arg_idx])
        arg_idx = arg_idx + 1

        local fields = {}
        for j = 1, n_fields do
            fields[#fields + 1] = ARGV[arg_idx]
            arg_idx = arg_idx + 1
        end

        local values = redis.call("HMGET", key, unpack(fields))

        -- return: [key, fields[], values[]]
        table.insert(res, key)
        table.insert(res, fields)
        table.insert(res, values)
    end

    return res
    """
