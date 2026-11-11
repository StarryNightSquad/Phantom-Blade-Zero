--[[
BaiyiDiag v4 - STRICTLY READ-ONLY runtime diagnosis.

History: BaiyiUnlock v1/v2 crashed (0xC0000005) because they called
comp:UnlockOutfit(id); pcall cannot catch a bad UFunction call. This script
calls NO UFunction at all. It only uses FindAllOf / StaticFindObject,
property reads, and UE4SS Lua binding helpers.

v4 changes (playtest 08:49):
  * delay 20 s (the appearance component did not exist at 12 s: components=0,
    while BaiyiUnlock saw it 5 s later).
  * dump the CONTENTS of OwnedOutfits / DefaultOutfits / UnlockedIds, not just
    their types. Several read-only traversal strategies are tried, each pcall
    protected, so we learn exactly which base-game ItemIds the player owns.
  * dump RowMap keys of both tables to prove whether our row was merged.

Goal: if v4's borrowed ItemId still shows "未解锁", the log tells us the exact
ID to use next time - no more blind configuration changes.
--]]
local TAG = "[BaiyiDiag]"
local FIRST_DELAY = 20000

local function log(fmt, ...)
    local ok, s = pcall(string.format, fmt, ...)
    print(TAG .. " " .. (ok and s or tostring(fmt)) .. "\n")
end

local function TRY(fn)
    local ok, r = pcall(fn)
    if ok then return r end
    return nil
end

local function full(o)
    return TRY(function() return o:GetFullName() end) or "?"
end

local function show(v)
    if v == nil then return "<nil>" end
    local s = tostring(v)
    return (#s > 160) and (s:sub(1, 160) .. "...") or s
end

-- Try several read-only ways to enumerate a UE4SS container userdata.
local function dump_container(label, v)
    if v == nil then
        log("  %-24s <nil>", label)
        return
    end
    log("  %-24s type=%s tostring=%s", label, type(v), show(v))
    if type(v) ~= "userdata" then return end

    local n = TRY(function() return v:GetArrayNum() end)
    log("      GetArrayNum=%s", show(n))
    if n ~= nil and tonumber(n) and tonumber(n) > 0 then
        local lim = math.min(tonumber(n), 30)
        for i = 1, lim do
            local e = TRY(function() return v:Get(i) end)
            log("      [%d] %s", i, show(e))
        end
    end

    local okfe, fe = pcall(function()
        local seen = 0
        v:ForEach(function(idx, elem)
            if seen < 30 then log("      ForEach[%s] %s", show(idx), show(elem)) end
            seen = seen + 1
        end)
        return seen
    end)
    log("      ForEach ok=%s count=%s", tostring(okfe), show(fe))

    local okp, cnt = pcall(function()
        local c = 0
        for k, val in pairs(v) do
            if c < 30 then log("      pairs[%s] %s", show(k), show(val)) end
            c = c + 1
        end
        return c
    end)
    log("      pairs ok=%s count=%s", tostring(okp), show(cnt))

    local nm = TRY(function() return v:GetFullName() end)
    if nm then log("      fullname=%s", show(nm)) end
end

local COMP_PROPS = {
    "OwnedOutfits", "CachedOwnedOutfits", "UnlockedIds", "DefaultOutfits",
    "OutfitIDs", "CachedOutfit", "CurrentOutfit", "bForceDefaultAppearance",
}

local function probeComponent(c)
    log("=== COMPONENT %s", full(c))
    local cls = TRY(function() return c:GetClass() end)
    if cls then log("  class=%s", full(cls)) end
    for _, p in ipairs(COMP_PROPS) do
        dump_container(p, TRY(function() return c[p] end))
    end
end

local function probeTableObject(o, label)
    log("=== TABLE %s :: %s", label, full(o))
    dump_container("ParentTables", TRY(function() return o.ParentTables end))
    dump_container("RowMap", TRY(function() return o.RowMap end))
    log("  RowStruct=%s", show(TRY(function() return o.RowStruct end)))
end

local function probeTables()
    for _, cn in ipairs({ "DataTable", "CompositeDataTable" }) do
        local arr = TRY(function() return FindAllOf(cn) end)
        if arr then
            log("=== FindAllOf(%s) count=%d", cn, #arr)
            for _, o in ipairs(arr) do
                local f = full(o)
                if f:find("Baiyi") or f:find("AppearanceTable")
                   or f:find("CollectionGrants") or f:find("PBZOutfitSlots") then
                    probeTableObject(o, cn)
                end
            end
        else
            log("=== FindAllOf(%s) returned nil", cn)
        end
    end

    for _, path in ipairs({
        "/Game/Mods/PBZOutfitSlots/DT_BaiyiAppearance.DT_BaiyiAppearance",
        "/Game/PBZContent/DataTable/UI/DT_PBZAppearanceTable.DT_PBZAppearanceTable",
    }) do
        local o = TRY(function() return StaticFindObject(path) end)
        log("=== StaticFindObject(%s) -> %s", path, o and full(o) or "<nil>")
        if o then probeTableObject(o, "StaticFindObject") end
    end
end

log("read-only diagnostic v4, starting in %d s", math.floor(FIRST_DELAY / 1000))
ExecuteWithDelay(FIRST_DELAY, function()
    local comps = {}
    for _, cn in ipairs({ "PBZAppearanceComponent", "BP_AppearanceComp_C",
                          "AppearanceComponent", "PBZAppearanceComp_C" }) do
        local arr = TRY(function() return FindAllOf(cn) end)
        if arr then
            for _, o in ipairs(arr) do comps[#comps + 1] = o end
        end
    end
    log("components=%d", #comps)
    for _, c in ipairs(comps) do probeComponent(c) end
    probeTables()
    log("=== DONE (no UFunction was called)")
end)
