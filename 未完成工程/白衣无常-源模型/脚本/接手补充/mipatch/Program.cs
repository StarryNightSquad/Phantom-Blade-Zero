using UAssetAPI;
using UAssetAPI.UnrealTypes;
using UAssetAPI.Unversioned;
using UAssetAPI.ExportTypes;

// mipatch read  <file.uasset> [mappings.usmap]
// mipatch patch <file.uasset> <out.uasset> [mappings.usmap]
internal static class Program
{
    // PropertyData subclasses hold the payload in a public field/property named Value.
    private static string ReadValue(object p)
    {
        var t = p.GetType();
        var pi = t.GetProperty("Value", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
        if (pi is not null)
        {
            try { return pi.GetValue(p)?.ToString() ?? "null"; } catch { /* fall through */ }
        }
        var fi = t.GetField("Value", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
        if (fi is not null)
        {
            try { return fi.GetValue(p)?.ToString() ?? "null"; } catch { /* fall through */ }
        }
        return p.ToString() ?? "?";
    }

    // Recursively walk ArrayPropertyData / StructPropertyData contents.
    private static void DumpProp(object p, int depth)
    {
        var ind = new string(' ', 2 + depth * 2);
        var name = p.GetType().GetProperty("Name")?.GetValue(p)?.ToString() ?? "?";
        var val = ReadValue(p);
        if (val.Length > 200) val = val[..200];
        Console.WriteLine(ind + name + " [" + p.GetType().Name + "] = " + val);
        if (depth >= 4) return;

        var t = p.GetType();
        var vProp = t.GetProperty("Value", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
        var raw = vProp?.GetValue(p);
        if (raw is System.Collections.IEnumerable en && raw is not string)
        {
            var i = 0;
            foreach (var item in en)
            {
                if (item is null) continue;
                var it = item.GetType();
                if (it.Name.Contains("PropertyData"))
                    DumpProp(item, depth + 1);
                else
                    Console.WriteLine(ind + "  [" + i + "] " + it.Name + " = " + item);
                i++;
                if (i > 40) { Console.WriteLine(ind + "  ... truncated"); break; }
            }
        }
    }

    private static int Main(string[] args)
    {
        if (args.Length < 2) { Console.WriteLine("usage: mipatch read|patch <in.uasset> [out.uasset] [usmap]"); return 1; }
        var mode = args[0];
        var path = args[1];
        Usmap map = null;
        foreach (var a in args) if (a.EndsWith(".usmap", StringComparison.OrdinalIgnoreCase)) map = new Usmap(a);

        // fromjson <in.json> <out.uasset> [usmap] : JSON -> UAsset -> Write.
        if (mode.Equals("fromjson", StringComparison.OrdinalIgnoreCase))
        {
            var json = File.ReadAllText(path);
            var rebuilt = UAsset.DeserializeJson(json);
            if (map is not null) rebuilt.Mappings = map;
            rebuilt.Write(args[2]);
            Console.WriteLine("WROTE_UASSET " + args[2]);
            return 0;
        }

        var engineName = Environment.GetEnvironmentVariable("MIPATCH_ENGINE") ?? "VER_UE5_7";
        var engine = (EngineVersion)Enum.Parse(typeof(EngineVersion), engineName);
        Console.WriteLine("EngineVersion: " + engine);
        var asset = new UAsset(path, engine, map);
        Console.WriteLine("File: " + path);
        Console.WriteLine("Exports: " + asset.Exports.Count);
        Console.WriteLine("Mappings: " + (map is null ? "none" : "loaded"));

        // tojson <in.uasset> <out.json> [usmap] : full UAsset -> JSON (imports, names, exports, row data).
        if (mode.Equals("tojson", StringComparison.OrdinalIgnoreCase))
        {
            var outJson = args[2];
            var json = asset.SerializeJson(Newtonsoft.Json.Formatting.Indented);
            File.WriteAllText(outJson, json, System.Text.Encoding.UTF8);
            Console.WriteLine("WROTE_JSON " + json.Length + " chars -> " + outJson);
            return 0;
        }

        foreach (var e in asset.Exports)
        {
            var label = e.ObjectName?.ToString() ?? "?";
            Console.WriteLine("EXPORT " + label + " [" + e.GetType().Name + "]");
            if (e is not NormalExport ne) continue;
            foreach (var p in ne.Data) DumpProp(p, 1);
        }
        if (mode == "read") return 0;

        var outPath = args[2];
        var target = Environment.GetEnvironmentVariable("MIPATCH_PARAM") ?? "Albedo Controls";
        var changed = 0;
        foreach (var e in asset.Exports)
            if (e is NormalExport ne2)
                foreach (var p in ne2.Data) changed += PatchNode(p, target);
        Console.WriteLine("PATCHED " + changed + " LinearColor value(s) for param '" + target + "'");
        if (changed == 0) { Console.WriteLine("Nothing changed, not writing."); return 2; }
        asset.Write(outPath);
        Console.WriteLine("WROTE " + outPath);
        return 0;
    }

    private static object RawValue(object p) =>
        p.GetType().GetProperty("Value", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance)?.GetValue(p);

    private static IEnumerable<object> Children(object p)
    {
        var raw = RawValue(p);
        if (raw is System.Collections.IEnumerable en && raw is not string)
            foreach (var x in en) if (x is not null) yield return x;
    }

    private static string FindName(object node)
    {
        if (node.GetType().Name == "NamePropertyData") return ReadValue(node);
        foreach (var c in Children(node))
        {
            var s = FindName(c);
            if (!string.IsNullOrEmpty(s)) return s;
        }
        return "";
    }

    private static void CollectColors(object node, List<object> outList)
    {
        if (node.GetType().Name == "LinearColorPropertyData") { outList.Add(node); return; }
        foreach (var c in Children(node)) CollectColors(c, outList);
    }

    private static int PatchNode(object node, string target)
    {
        var colors = new List<object>();
        CollectColors(node, colors);
        if (colors.Count > 0 && FindName(node) == target)
        {
            var n = 0;
            foreach (var c in colors) { SetPureRed(c); n++; }
            return n;
        }
        var changed = 0;
        foreach (var c in Children(node)) changed += PatchNode(c, target);
        return changed;
    }

    private static void SetPureRed(object colorProp)
    {
        var t = colorProp.GetType();
        var vp = t.GetProperty("Value", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance)!;
        var boxed = vp.GetValue(colorProp)!;
        var ct = boxed.GetType();
        Console.WriteLine("  LinearColor runtime type: " + ct.FullName);
        foreach (var (field, value) in new[] { ("R", 1f), ("G", 0f), ("B", 0f), ("A", 0f) })
        {
            var f = ct.GetField(field, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
            var pr = ct.GetProperty(field, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
            if (f is not null) f.SetValue(boxed, value);
            else if (pr is not null) pr.SetValue(boxed, value);
            else Console.WriteLine("  WARN: no R/G/B/A member '" + field + "'");
        }
        vp.SetValue(colorProp, boxed);
        Console.WriteLine("  set -> " + ReadValue(colorProp));
    }
}
