using System;
using System.Collections.Generic;
using System.Linq;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace SunThroughGrates
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public class Plugin : BaseUnityPlugin
    {
        public const string PluginGuid = "nickweedon.SunThroughGrates";
        public const string PluginName = "SunThroughGrates";
        public const string PluginVersion = "1.0.0";

        private const string DefaultIgnored =
            "iron_floor_1x1,iron_floor_2x2,iron_grate,iron_wall_1x1,iron_wall_2x2";

        internal static ConfigEntry<string> IgnoredPrefabs;
        internal static HashSet<string> IgnoredSet = new HashSet<string>();

        private Harmony _harmony;

        private void Awake()
        {
            IgnoredPrefabs = Config.Bind("General", "Ignored prefabs", DefaultIgnored,
                "Comma-separated prefab names that let sunlight through to plants below.");
            ParseIgnored();
            IgnoredPrefabs.SettingChanged += (_, _) => ParseIgnored();

            _harmony = Harmony.CreateAndPatchAll(typeof(PlantPatches), PluginGuid);
            Logger.LogInfo($"{PluginName} {PluginVersion} loaded; ignoring: {string.Join(", ", IgnoredSet)}");
        }

        private void OnDestroy() => _harmony?.UnpatchSelf();

        private static void ParseIgnored()
        {
            IgnoredSet = new HashSet<string>(
                IgnoredPrefabs.Value.Split(',').Select(s => s.Trim()).Where(s => s.Length > 0),
                StringComparer.OrdinalIgnoreCase);
        }
    }

    [HarmonyPatch]
    internal static class PlantPatches
    {
        // Same layers and range as vanilla Plant.HaveRoof()
        private static int _roofMask;
        private static readonly RaycastHit[] Hits = new RaycastHit[32];

        [HarmonyPatch(typeof(Plant), "HaveRoof")]
        [HarmonyPrefix]
        private static bool HaveRoofPrefix(Plant __instance, ref bool __result)
        {
            if (_roofMask == 0)
                _roofMask = LayerMask.GetMask("Default", "static_solid", "piece");

            int count = Physics.RaycastNonAlloc(__instance.transform.position, Vector3.up,
                Hits, 100f, _roofMask);

            __result = false;
            for (int i = 0; i < count; i++)
            {
                if (!IsIgnored(Hits[i].collider))
                {
                    __result = true;
                    break;
                }
            }
            return false;
        }

        private static bool IsIgnored(Collider collider)
        {
            if (collider == null)
                return false;

            // Pieces are networked objects; the ZNetView sits on the prefab root
            var nview = collider.GetComponentInParent<ZNetView>();
            if (nview == null)
                return false;

            return Plugin.IgnoredSet.Contains(Utils.GetPrefabName(nview.gameObject));
        }
    }
}
