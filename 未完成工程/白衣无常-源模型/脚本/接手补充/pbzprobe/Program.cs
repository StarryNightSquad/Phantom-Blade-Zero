using System.Reflection;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.UE4.Versions;

// Minimal CUE4Parse CLI for this project.
//   no args                                  -> toolchain smoke test
//   wcls <paksDir> <aesKey> [filter]         -> list matching asset paths
//   wextract <paksDir> <aesKey> <filter> <outDir> -> dump raw asset bytes
internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length == 0)
            return Smoke();
        if (args[0].Equals("umap", StringComparison.OrdinalIgnoreCase) && args.Length > 1)
            return UmapCheck(args[1]);
        // bpa <paksDir> <aesKey> <usmapPath> <assetFilter>
        if (args[0].Equals("bpa", StringComparison.OrdinalIgnoreCase) && args.Length > 4)
            return Bpa(args[1], args[2], args[3], args[4]);
        // dt <paksDir> <aesKey> <usmapPath> <assetFilter> : read a base-game
        // DataTable with UE5.7 settings (bpa is hard-coded to UE5.1 for Wuchang)
        if (args[0].Equals("dt", StringComparison.OrdinalIgnoreCase) && args.Length > 4)
            return Dt(args[1], args[2], args[3], args[4]);
        // slot <mountDir> <usmapPath> <assetFilter> : inspect a PBZ IoStore DataTable
        if (args[0].Equals("slot", StringComparison.OrdinalIgnoreCase) && args.Length > 3)
            return Slot(args[1], args[2], args[3]);
        // pcls <paksDir> <aesKey> <usmapPath> <filter> : list/extract from encrypted PBZ Paks
        if (args[0].Equals("pcls", StringComparison.OrdinalIgnoreCase) && args.Length > 4)
            return Pcls(args[1], args[2], args[3], args[4],
                args.Length > 5 ? args[5] : null);
        // skel <paksDir> <aesKey> <usmapPath> <assetFilter> <outFile>
        // Dump a cooked UE5.7 USkeleton's bone names by reflection (read-only).
        if (args[0].Equals("skel", StringComparison.OrdinalIgnoreCase) && args.Length > 5)
            return Skel(args[1], args[2], args[3], args[4], args[5]);

        try
        {
            var mode = args[0];
            var paksDir = args[1];
            var aesKey = args[2];
            var filter = args.Length > 3 ? args[3] : string.Empty;
            var filters = filter.Split('|', StringSplitOptions.RemoveEmptyEntries);
            var outDir = mode == "wextract" && args.Length > 4 ? args[4] : null;

            var provider = new DefaultFileProvider(
                paksDir,
                SearchOption.TopDirectoryOnly,
                true,
                new VersionContainer(EGame.GAME_UE5_1));
            provider.Initialize();
            provider.SubmitKey(new FGuid(), new FAesKey(aesKey));
            Console.WriteLine("Mounted files: " + provider.Files.Count);

            var hits = provider.Files
                .Where(kv => filters.Length == 0 ||
                             filters.Any(f => kv.Key.Contains(f, StringComparison.OrdinalIgnoreCase)))
                .OrderBy(kv => kv.Key, StringComparer.OrdinalIgnoreCase)
                .ToList();
            Console.WriteLine("Matches: " + hits.Count);
            foreach (var kv in hits.Take(300))
                Console.WriteLine("  " + kv.Key);

            if (outDir is not null)
            {
                Directory.CreateDirectory(outDir);
                var written = 0;
                var failed = 0;
                foreach (var kv in hits)
                {
                    try
                    {
                        var data = kv.Value.Read();
                        var rel = kv.Key.Replace('/', Path.DirectorySeparatorChar)
                            .TrimStart(Path.DirectorySeparatorChar);
                        var dst = Path.Combine(outDir, rel);
                        Directory.CreateDirectory(Path.GetDirectoryName(dst)!);
                        File.WriteAllBytes(dst, data);
                        written++;
                    }
                    catch (Exception ex)
                    {
                        failed++;
                        if (failed <= 5)
                            Console.Error.WriteLine("  skip " + kv.Key + " : " + ex.Message);
                    }
                }
                Console.WriteLine($"EXTRACTED {written} FAILED {failed}");
            }
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("FAIL: " + ex);
            return 1;
        }
    }

    // CUE4Parse mixes public fields and properties; read either.
    private static object? Member(object o, string n)
    {
        var t = o.GetType();
        var pi = t.GetProperty(n, BindingFlags.Public | BindingFlags.Instance);
        if (pi is not null)
        {
            try { return pi.GetValue(o); } catch { /* fall through */ }
        }
        var fi = t.GetField(n, BindingFlags.Public | BindingFlags.Instance);
        if (fi is not null)
        {
            try { return fi.GetValue(o); } catch { /* fall through */ }
        }
        return null;
    }

    private static string ReadMember(object o, string n) => Member(o, n)?.ToString() ?? "?";

    // FPropertyTag.Tag is a wrapper around the real value; peel up to 3 layers.
    private static object? Unwrap(object? v)
    {
        for (var i = 0; i < 3 && v is not null; i++)
        {
            var tn = v.GetType().Name;
            if (tn.Contains("FStructFallback") || tn.Contains("UScriptArray")
             || tn.Contains("UScriptMap") || tn.Contains("UScriptStruct")) break;
            object? next = null;
            foreach (var n in new[] { "StructType", "Value", "GenericValue", "Struct", "Array", "Map", "Data", "Inner" })
            {
                var cand = Member(v, n);
                if (cand is not null && !ReferenceEquals(cand, v)) { next = cand; break; }
            }
            if (next is null) break;
            v = next;
        }
        return v;
    }

    // Recursively expand FStructFallback / UScriptArray / UScriptMap containers.
    private static void Dump(object? v, string label, int depth, ref int hits)
    {
        var ind = new string(' ', 2 + depth * 2);
        if (v is null) { Console.WriteLine(ind + label + " = ?"); return; }
        v = Unwrap(v);
        if (v is null) { Console.WriteLine(ind + label + " = ?"); return; }
        var tn = v.GetType().Name;
        var props = FindProps(v);
        var isContainer = tn.Contains("FStructFallback") || tn.Contains("UScriptArray")
                       || tn.Contains("UScriptMap") || tn.Contains("FScriptStruct");
        if (isContainer && props is not null)
        {
            Console.WriteLine(ind + label + " [" + tn + "]");
            if (tn.Contains("FStructFallback") || tn.Contains("FScriptStruct"))
                Console.WriteLine(ind + "  STRUCTTYPE=" + ReadMember(v, "StructType"));
            if (depth >= 6) return;
            var i = 0;
            foreach (var q in props)
            {
                var qn = ReadMember(q, "Name");
                var qv = Member(q, "Tag");
                if (qn == "?" && qv is null) qv = q; // element is the value itself
                if (qn == "?" || qn == "None" || string.IsNullOrWhiteSpace(qn)) qn = "[" + i + "]";
                if (Interesting(qn)) hits++;
                Dump(qv, qn, depth + 1, ref hits);
                i++;
            }
            return;
        }
        var s = v.ToString() ?? "?";
        if (s.Length > 180) s = s[..180];
        if (Interesting(label)) hits++;
        Console.WriteLine(ind + label + " = " + s);
    }

    // Locate the FPropertyTag-like child collection regardless of member name / field-vs-property.
    private static System.Collections.IEnumerable? FindProps(object o)
    {
        foreach (var n in new[] { "Properties", "Fields", "Values", "Entries", "Items" })
            if (Member(o, n) is System.Collections.IEnumerable e) return e;
        foreach (var fi in o.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
            if (fi.GetValue(o) is System.Collections.IEnumerable e2 && fi.GetValue(o) is not string)
                return e2;
        foreach (var pi in o.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (pi.GetIndexParameters().Length > 0) continue;
            try
            {
                if (pi.GetValue(o) is System.Collections.IEnumerable e3 && pi.GetValue(o) is not string)
                    return e3;
            }
            catch { /* skip */ }
        }
        return null;
    }

    private static readonly string[] Wanted =
    {
        "SpringStiffness", "SpringDamping", "TrailBone", "ChainBoneAxis",
        "RotationBlendAlpha", "AlphaCurveName", "BoneName", "RootBoneToCopy",
        "CopyCurves", "BlendWeight", "Stiffness", "Damping", "Relaxation",
        "TrailRelaxationSpeed", "SimSpace", "Alpha", "Limit", "Bone", "Speed", "Scale"
    };

    private static bool Interesting(string name) =>
        Wanted.Any(w => name.Contains(w, StringComparison.OrdinalIgnoreCase));

    // skel : read-only reflection dump of a cooked USkeleton, so we can compare its
    // bone names with the FBX we are about to import. UE5.7 + PBZ usmap required.
    private static int Skel(string paksDir, string aesKey, string usmapPath, string filter,
        string outFile)
    {
        var provider = new DefaultFileProvider(
            paksDir, SearchOption.TopDirectoryOnly, true,
            new VersionContainer(EGame.GAME_UE5_7));
        provider.Initialize();
        provider.SubmitKey(new FGuid(), new FAesKey(aesKey));

        var asm = Assembly.Load("CUE4Parse");
        var ut = asm.GetType("CUE4Parse.MappingsProvider.Usmap.FileUsmapTypeMappingsProvider");
        if (ut is not null && File.Exists(usmapPath))
        {
            var mappings = Activator.CreateInstance(ut,
                new object?[] { usmapPath, StringComparer.OrdinalIgnoreCase })!;
            PropertyInfo? mp = null;
            for (var t = provider.GetType(); t is not null && mp is null; t = t.BaseType)
                mp = t.GetProperty("MappingsContainer",
                    BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
            mp?.SetValue(provider, mappings);
        }

        var lines = new List<string>();
        var visited = new HashSet<object>(ReferenceEqualityComparer.Instance);
        var keys = provider.Files.Keys
            .Where(k => k.Contains(filter, StringComparison.OrdinalIgnoreCase))
            .OrderBy(k => k, StringComparer.OrdinalIgnoreCase).ToList();
        Console.WriteLine("Assets: " + keys.Count);
        foreach (var key in keys)
        {
            lines.Add("ASSET " + key);
            try
            {
                var pkg = provider.LoadPackage(key);
                if (Member(pkg, "NameMap") is System.Collections.IEnumerable nameMap)
                {
                    var ni = 0;
                    foreach (var ne in nameMap)
                        lines.Add("NAME " + ni++ + " = " + ReadMember(ne!, "Name"));
                }
                if (Member(pkg, "ImportMap") is System.Collections.IEnumerable importMap)
                {
                    var ii = 0;
                    foreach (var im in importMap)
                    {
                        lines.Add("IMPORT " + ii);
                        SkelWalk(im!, "IMPORT[" + ii + "]", 0, lines, visited);
                        ii++;
                    }
                }
                foreach (var e in pkg.GetExports())
                {
                    lines.Add("EXPORT " + ReadMember(e, "Name") + " TYPE " + e.GetType().FullName);
                    SkelWalk(e, "e", 0, lines, visited);
                }
            }
            catch (Exception ex) { lines.Add("LOAD_FAILED " + ex.Message); }
        }
        File.WriteAllLines(outFile, lines);
        Console.WriteLine("SKEL_DUMP " + lines.Count + " lines -> " + outFile);
        return 0;
    }

    private static readonly HashSet<string> SkelSkip = new(StringComparer.OrdinalIgnoreCase)
        { "Owner", "Outer", "Package", "Provider", "Super", "Class", "Template", "ExportType" };

    private static void SkelWalk(object? v, string path, int depth, List<string> lines,
        HashSet<object> visited)
    {
        if (v is null || depth > 7 || lines.Count > 400000) return;
        var t = v.GetType();
        var tn = t.FullName ?? t.Name;
        if (tn.StartsWith("System.") && v is not System.Collections.IEnumerable)
        {
            lines.Add(path + " = " + (v.ToString() ?? "?"));
            return;
        }
        if (v is string || tn.Contains("FName") || tn.Contains("FString") ||
            t.IsPrimitive || t.IsEnum)
        {
            var s = v.ToString() ?? "?";
            if (s.Length > 300) s = s[..300];
            lines.Add(path + " = " + s);
            return;
        }
        if (!visited.Add(v)) return;
        if (v is System.Collections.IEnumerable en)
        {
            var i = 0;
            foreach (var item in en)
            {
                SkelWalk(item, path + "[" + i + "]", depth + 1, lines, visited);
                if (++i > 8000) { lines.Add(path + " ...TRUNCATED"); break; }
            }
            return;
        }
        foreach (var pi in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (SkelSkip.Contains(pi.Name) || pi.GetIndexParameters().Length > 0) continue;
            object? cv;
            try { cv = pi.GetValue(v); } catch { continue; }
            SkelWalk(cv, path + "." + pi.Name, depth + 1, lines, visited);
        }
        foreach (var fi in t.GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            if (SkelSkip.Contains(fi.Name)) continue;
            object? cv;
            try { cv = fi.GetValue(v); } catch { continue; }
            SkelWalk(cv, path + "." + fi.Name, depth + 1, lines, visited);
        }
    }

    // pcls : mount the encrypted PBZ game Paks (UE5.7) and list matching assets.
    private static int Pcls(string paksDir, string aesKey, string usmapPath, string filter,
        string? outDir)
    {
        var provider = new DefaultFileProvider(
            paksDir, SearchOption.TopDirectoryOnly, true,
            new VersionContainer(EGame.GAME_UE5_7));
        provider.Initialize();
        provider.SubmitKey(new FGuid(), new FAesKey(aesKey));
        Console.WriteLine("Mounted files: " + provider.Files.Count);

        var asm = Assembly.Load("CUE4Parse");
        var ut = asm.GetType("CUE4Parse.MappingsProvider.Usmap.FileUsmapTypeMappingsProvider");
        if (ut is not null && File.Exists(usmapPath))
        {
            var mappings = Activator.CreateInstance(ut,
                new object?[] { usmapPath, StringComparer.OrdinalIgnoreCase })!;
            PropertyInfo? mp = null;
            for (var t = provider.GetType(); t is not null && mp is null; t = t.BaseType)
                mp = t.GetProperty("MappingsContainer",
                    BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
            mp?.SetValue(provider, mappings);
            Console.WriteLine("MappingsContainer set: " + (mp is not null));
        }

        // Special filter: dump every asset path to a text file for offline grepping.
        if (filter.Equals("!index", StringComparison.OrdinalIgnoreCase))
        {
            var all = provider.Files.Keys
                .OrderBy(k => k, StringComparer.OrdinalIgnoreCase).ToList();
            var dest = outDir ?? Path.Combine(Directory.GetCurrentDirectory(), "pbz_index.txt");
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(dest))!);
            File.WriteAllLines(dest, all);
            Console.WriteLine("INDEX_WRITTEN " + all.Count + " -> " + dest);
            return 0;
        }

        var hits = provider.Files.Keys
            .Where(k => k.Contains(filter, StringComparison.OrdinalIgnoreCase))
            .OrderBy(k => k, StringComparer.OrdinalIgnoreCase)
            .Take(60)
            .ToList();
        Console.WriteLine("Matches (first 60): " + hits.Count);
        foreach (var k in hits) Console.WriteLine("  " + k);

        if (outDir is not null)
        {
            Directory.CreateDirectory(outDir);
            var written = 0;
            foreach (var k in hits)
            {
                try
                {
                    var data = provider.Files[k].Read();
                    var dst = Path.Combine(outDir,
                        k.Replace('/', Path.DirectorySeparatorChar).TrimStart(Path.DirectorySeparatorChar));
                    Directory.CreateDirectory(Path.GetDirectoryName(dst)!);
                    File.WriteAllBytes(dst, data);
                    written++;
                }
                catch (Exception ex) { Console.WriteLine("  skip " + k + " : " + ex.Message); }
            }
            Console.WriteLine("EXTRACTED " + written);
        }
        return 0;
    }

    // dt : read a cooked DataTable from the ENCRYPTED base-game containers.
    // bpa is hard-coded to GAME_UE5_1 (Wuchang); PBZ is 5.7.4 and Zen packages
    // fail to deserialize with the wrong version. This uses GAME_UE5_7 + AES.
    private static int Dt(string paksDir, string aesKey, string usmapPath, string filter)
    {
        var provider = new DefaultFileProvider(
            paksDir, SearchOption.TopDirectoryOnly, true,
            new VersionContainer(EGame.GAME_UE5_7));
        provider.Initialize();
        provider.SubmitKey(new FGuid(), new FAesKey(aesKey));
        Console.WriteLine("Mounted files: " + provider.Files.Count);

        var asm = Assembly.Load("CUE4Parse");
        var ut = asm.GetType("CUE4Parse.MappingsProvider.Usmap.FileUsmapTypeMappingsProvider")
            ?? throw new Exception("FileUsmapTypeMappingsProvider not found");
        var mappings = Activator.CreateInstance(ut,
            new object?[] { usmapPath, StringComparer.OrdinalIgnoreCase })!;
        PropertyInfo? mp = null;
        for (var t = provider.GetType(); t is not null && mp is null; t = t.BaseType)
            mp = t.GetProperty("MappingsContainer",
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
        mp?.SetValue(provider, mappings);
        Console.WriteLine("MappingsContainer set: " + (mp is not null));

        var key = provider.Files.Keys.FirstOrDefault(k =>
            k.Contains(filter, StringComparison.OrdinalIgnoreCase)
            && k.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase));
        if (key is null) throw new Exception("no asset matches: " + filter);
        Console.WriteLine("Asset: " + key);

        var pkg = provider.LoadPackage(key);
        Console.WriteLine("Package loaded: " + pkg.GetType().FullName);
        var hits = 0;
        foreach (var e in pkg.GetExports())
        {
            Console.WriteLine("EXPORT name=" + ReadMember(e, "Name")
                + " type=" + ReadMember(e, "ExportType")
                + " runtime=" + e.GetType().FullName);
            try
            {
                var props = Member(e, "Properties") as System.Collections.IEnumerable;
                if (props is not null)
                    foreach (var p in props)
                        Dump(Member(p, "Tag"), ReadMember(p, "Name"), 1, ref hits);

                var rowMap = Member(e, "RowMap") as System.Collections.IEnumerable;
                if (rowMap is null) continue;
                var n = 0;
                foreach (var row in rowMap)
                {
                    var rk = ReadMember(row, "Key");
                    var rv = Member(row, "Value");
                    if (rk == "?" && rv is null) rv = row;
                    Console.WriteLine("  ROW[" + n + "] key=" + rk);
                    Dump(rv, "row", 2, ref hits);
                    n++;
                }
                Console.WriteLine("ROWS " + n);
            }
            catch (Exception ex)
            {
                Console.WriteLine("EXPORT_ERROR " + ex);
            }
        }
        Console.WriteLine("DONE");
        return 0;
    }

    // slot : mount a PBZ IoStore mod container (UE5.7) and dump a DataTable's rows.
    private static int Slot(string dir, string usmapPath, string filter)
    {
        var provider = new DefaultFileProvider(
            dir, SearchOption.TopDirectoryOnly, true,
            new VersionContainer(EGame.GAME_UE5_7));
        provider.Initialize();
        Console.WriteLine("Mounted files: " + provider.Files.Count);
        foreach (var k in provider.Files.Keys.Take(20)) Console.WriteLine("  " + k);

        var asm = Assembly.Load("CUE4Parse");
        var ut = asm.GetType("CUE4Parse.MappingsProvider.Usmap.FileUsmapTypeMappingsProvider")
            ?? throw new Exception("FileUsmapTypeMappingsProvider not found");
        var mappings = Activator.CreateInstance(ut,
            new object?[] { usmapPath, StringComparer.OrdinalIgnoreCase })!;
        PropertyInfo? mp = null;
        for (var t = provider.GetType(); t is not null && mp is null; t = t.BaseType)
            mp = t.GetProperty("MappingsContainer",
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
        mp?.SetValue(provider, mappings);
        Console.WriteLine("MappingsContainer set: " + (mp is not null));

        var key = provider.Files.Keys.FirstOrDefault(k =>
            k.Contains(filter, StringComparison.OrdinalIgnoreCase)
            && k.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase));
        if (key is null) throw new Exception("no asset matches: " + filter);
        Console.WriteLine("Asset: " + key);

        var pkg = provider.LoadPackage(key);
        var hits = 0;
        foreach (var e in pkg.GetExports())
        {
            Console.WriteLine("EXPORT name=" + ReadMember(e, "Name")
                + " type=" + ReadMember(e, "ExportType"));
            var props = Member(e, "Properties") as System.Collections.IEnumerable;
            if (props is not null)
                foreach (var p in props)
                    Dump(Member(p, "Tag"), ReadMember(p, "Name"), 1, ref hits);

            var rowMap = Member(e, "RowMap") as System.Collections.IEnumerable;
            if (rowMap is null) continue;
            var n = 0;
            foreach (var row in rowMap)
            {
                var rk = ReadMember(row, "Key");
                var rv = Member(row, "Value");
                if (rk == "?" && rv is null) rv = row;
                Console.WriteLine("  ROW[" + n + "] key=" + rk);
                Dump(rv, "row", 2, ref hits);
                n++;
            }
            Console.WriteLine("ROWS " + n);
        }
        Console.WriteLine("DONE");
        return 0;
    }

    // bpa : load a cooked AnimBlueprint with usmap mappings and dump export properties.
    // Reflection-only so it survives CUE4Parse API changes.
    private static int Bpa(string paksDir, string aesKey, string usmapPath, string filter)
    {
        var provider = new DefaultFileProvider(
            paksDir, SearchOption.TopDirectoryOnly, true,
            new VersionContainer(EGame.GAME_UE5_1));
        provider.Initialize();
        provider.SubmitKey(new FGuid(), new FAesKey(aesKey));
        Console.WriteLine("Mounted files: " + provider.Files.Count);

        var asm = Assembly.Load("CUE4Parse");
        var ut = asm.GetType("CUE4Parse.MappingsProvider.Usmap.FileUsmapTypeMappingsProvider")
            ?? throw new Exception("FileUsmapTypeMappingsProvider not found");
        var mappings = Activator.CreateInstance(ut, new object?[] { usmapPath, StringComparer.OrdinalIgnoreCase })!;

        PropertyInfo? mp = null;
        for (var t = provider.GetType(); t is not null && mp is null; t = t.BaseType)
            mp = t.GetProperty("MappingsContainer",
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
        if (mp is not null)
        {
            mp.SetValue(provider, mappings);
            Console.WriteLine("MappingsContainer set via " + mp.DeclaringType?.Name);
        }
        else Console.WriteLine("WARN: MappingsContainer property not found");

        var filters = filter.Split('|', StringSplitOptions.RemoveEmptyEntries);
        var keys = provider.Files.Keys
            .Where(k => k.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase)
                     && filters.Any(f => k.Contains(f, StringComparison.OrdinalIgnoreCase)))
            .OrderBy(k => k, StringComparer.OrdinalIgnoreCase)
            .ToList();
        Console.WriteLine("Assets: " + keys.Count);

        var totalHits = 0;
        foreach (var key in keys)
        {
            Console.WriteLine();
            Console.WriteLine("===== ASSET " + key + " =====");
            try
            {
                var pkg = provider.LoadPackage(key);
                var exports = pkg.GetExports();
                Console.WriteLine("Exports: " + exports.Count());
                var hitCount = 0;
                foreach (var e in exports)
                {
                    Console.WriteLine("  EXPORT name=" + ReadMember(e, "Name")
                        + " type=" + ReadMember(e, "ExportType"));
                    var props = Member(e, "Properties") as System.Collections.IEnumerable;
                    if (props is null) continue;
                    foreach (var p in props)
                    {
                        var name = ReadMember(p, "Name");
                        var tagObj = Member(p, "Tag");
                        var expand = name.Contains("AnimGraphNode", StringComparison.OrdinalIgnoreCase)
                                  || name.Contains("AnimNodeData", StringComparison.OrdinalIgnoreCase)
                                  || name.Contains("Jiggle", StringComparison.OrdinalIgnoreCase)
                                  || name.Contains("Spring", StringComparison.OrdinalIgnoreCase);
                        if (expand) Dump(tagObj, name, 1, ref hitCount);
                        else
                        {
                            var s = tagObj?.ToString() ?? "?";
                            if (s.Length > 180) s = s[..180];
                            if (Interesting(name)) hitCount++;
                            Console.WriteLine("      " + name + " = " + s);
                        }
                    }
                }
                Console.WriteLine("INTERESTING_PROPS " + hitCount);
                totalHits += hitCount;
            }
            catch (Exception ex)
            {
                Console.WriteLine("  LOAD_FAILED " + ex.Message);
            }
        }
        Console.WriteLine("TOTAL_ASSETS " + keys.Count + " TOTAL_INTERESTING " + totalHits);
        return 0;
    }

    // umap <Mappings.usmap> : verify CUE4Parse can parse this usmap version.
    // Uses reflection so it works regardless of the exact Usmap ctor signature.
    private static int UmapCheck(string path)
    {
        var asm = Assembly.Load("CUE4Parse");
        var candidates = asm.GetTypes()
            .Where(x => x.Name.Contains("Usmap", StringComparison.OrdinalIgnoreCase)
                     || x.Name.Contains("Mapping", StringComparison.OrdinalIgnoreCase))
            .ToList();
        Console.WriteLine("candidate types (" + candidates.Count + "):");
        foreach (var c in candidates) Console.WriteLine("  " + c.FullName);
        var t = candidates.FirstOrDefault(x => x.Name == "FileUsmapTypeMappingsProvider")
             ?? candidates.FirstOrDefault(x => x.Name == "UsmapParser")
             ?? candidates.FirstOrDefault(x => x.Name.Contains("Usmap", StringComparison.OrdinalIgnoreCase)
                                            && !x.IsInterface && !x.IsAbstract && !x.IsEnum)
             ?? throw new Exception("no mappings type found");
        Console.WriteLine("selected type: " + t.FullName);
        foreach (var c in t.GetConstructors())
            Console.WriteLine("  ctor(" + string.Join(", ", c.GetParameters()
                .Select(p => p.ParameterType.Name + " " + p.Name)) + ")");

        object? inst = null;
        foreach (var c in t.GetConstructors())
        {
            var ps = c.GetParameters();
            var argv = new object?[ps.Length];
            var streams = new List<System.IO.Stream>();
            var ok = true;
            for (var i = 0; i < ps.Length; i++)
            {
                var pt = ps[i].ParameterType;
                if (pt == typeof(string)) argv[i] = i == 0 ? path : string.Empty;
                else if (pt == typeof(byte[])) argv[i] = File.ReadAllBytes(path);
                else if (typeof(System.IO.Stream).IsAssignableFrom(pt))
                {
                    var s = File.OpenRead(path); streams.Add(s); argv[i] = s;
                }
                else if (ps[i].HasDefaultValue) argv[i] = ps[i].DefaultValue;
                else if (pt.IsEnum) argv[i] = Enum.ToObject(pt, 0);
                else { ok = false; break; }
            }
            if (!ok) { foreach (var s in streams) s.Dispose(); continue; }
            try
            {
                inst = c.Invoke(argv);
                Console.WriteLine("  instantiated via " + c);
                break;
            }
            catch (Exception ex)
            {
                Console.WriteLine("  ctor failed: " + (ex.InnerException?.Message ?? ex.Message));
            }
            foreach (var s in streams) s.Dispose();
        }
        if (inst is null) throw new Exception("could not instantiate Usmap");

        foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            try
            {
                var v = p.GetValue(inst);
                var desc = v is System.Collections.ICollection col
                    ? "count=" + col.Count
                    : v?.ToString() ?? "null";
                Console.WriteLine("  " + p.Name + " (" + p.PropertyType.Name + ") = " + desc);
                if (v is not null && v.GetType().Name == "TypeMappings")
                {
                    foreach (var p2 in v.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                    {
                        try
                        {
                            var v2 = p2.GetValue(v);
                            var d2 = v2 is System.Collections.ICollection c2
                                ? "count=" + c2.Count
                                : v2?.ToString() ?? "null";
                            Console.WriteLine("      " + p2.Name + " (" + p2.PropertyType.Name + ") = " + d2);
                        }
                        catch { /* skip */ }
                    }
                }
            }
            catch { /* skip indexers / throwing getters */ }
        }
        Console.WriteLine("USMAP_LOAD_OK");
        return 0;
    }

    private static int Smoke()
    {
        try
        {
            var asm = Assembly.Load("CUE4Parse");
            Console.WriteLine("CUE4Parse assembly: " + asm.FullName);
            var gameEnum = asm.GetType("CUE4Parse.UE4.Versions.EGame");
            if (gameEnum is not null)
            {
                var names = Enum.GetNames(gameEnum);
                Console.WriteLine("Has GAME_UE5_7: " + names.Contains("GAME_UE5_7"));
                Console.WriteLine("Has GAME_UE5_8: " + names.Contains("GAME_UE5_8"));
            }
            Console.WriteLine("TOOLCHAIN_OK");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("TOOLCHAIN_FAIL: " + ex);
            return 1;
        }
    }
}
