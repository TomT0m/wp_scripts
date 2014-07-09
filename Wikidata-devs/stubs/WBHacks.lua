p = {}


local json = require('Module:JSON')
-- local io = require("io")
local http = require("socket.http")
local ltn12 = require("ltn12")

local p = {}
 
function p.entityJsonFromId(id)
	local URL = "http://www.wikidata.org/wiki/Special:EntityData/" .. id .. ".json"
	print(URL)
	local respbody={}
	local content = http.request{url=URL,
					sink=ltn12.sink.table(respbody)}
	
	-- https://www.wikidata.org/wiki/Special:EntityData/Q1.json
    	-- print(content ..  auth )
	return table.concat(respbody) -- content	
end

function p.get( id )
    --this just returns the json object of the id
    local id = id
    if string.find(id, "P") ~= nil then
        if string.find(id, "Property") == nil then
            id = "Property:" .. id
        end
    end
    
        

    -- local pg = mw.title.new(id):getContent()
    local pg = p.entityJsonFromId(id)
    -- print(pg)
    return json:decode(pg)
end
 
function p.thing(obj, typ, lang)
    -- Can be used to fetch either label or description, depends on what you want.
    local x = obj[typ][lang]
    if x == nil then
        x = obj[typ].en -- fallback to english
    end
    return x
end
 
function p.label(frame)
    local pframe = frame:getParent()
    local config = frame.args
    local args = pframe.args
 
    local qid = config.qid
    local lang = config.lang
    local obj = p.get(qid)
    return obj and p.thing(obj, "label", lang) or "(no label)"
end
 
function p.description(frame)
    local pframe = frame:getParent()
    local config = frame.args
    local args = pframe.args
 
    local qid = config.qid
    local lang = config.lang
    local obj = p.get(qid)
    return p.thing(obj, "description", lang)
 
end
 
 function p.howmany(frame)
    local pframe = frame:getParent()
    local config = frame.args
    local args = pframe.args
 
    local qid = config.qid
    local obj = p.get(qid)
    local count = 0
    for language,value in pairs(obj[config.what]) do
        count=count+1
    end
    return count
end
 
 function p.datatype(frame)
    local pframe = frame:getParent()
    local config = frame.args
    local args = pframe.args
 
    local qid = config.qid
    local obj = p.get(qid)
    return obj["datatype"]
 
end
 
return p



