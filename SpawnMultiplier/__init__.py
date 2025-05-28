from typing import Any
from argparse import Namespace
import unrealsdk #type: ignore
from mods_base import build_mod, hook, ENGINE, SliderOption, keybind, BoolOption, get_pc, command #type: ignore
from unrealsdk.hooks import Type , Block #type: ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type: ignore
from ui_utils import show_hud_message #type: ignore
EnemySlider: SliderOption = SliderOption("Enemy Multiplier", 4, 1, 25, 1, True)
EnableSpawnPoints: BoolOption = BoolOption("Create Additional Spawn Points", True, "Enabled", "Disabled",)

@command("force_multiplier", description="Override the slider and set a multiplier value")
def setMultiplier(args: Namespace) -> None:
    EnemySlider.value = int(args.multiplierValue)

setMultiplier.add_argument("multiplierValue", help="the multiplier to set, no guarentees it will be stable")

@hook("/Script/Engine.PlayerController:ServerNotifyLoadedWorld", Type.POST)
def SpawnMultiply(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    for den in unrealsdk.find_all("SpawnerStyle_Den", exact=False)[1:]:
        den.SpawnDelay = 0
        den.WaveDelay = 0
        den.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value
        den.MaxAliveActorsWhenPassive.AttributeInitializationData.BaseValueScale = EnemySlider.value
        den.MaxAliveActorsWhenThreatened.AttributeInitializationData.BaseValueScale = EnemySlider.value

    for bunch in unrealsdk.find_all("SpawnerStyle_Bunch", exact=False)[1:]:
        bunch.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value

    for bunchlist in unrealsdk.find_all("SpawnerStyle_BunchList", exact=False)[1:]:
        for bunch in bunchlist.bunches:
            bunch.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value
            bunch.NumActorsParam.Range.Value = EnemySlider.value

    for encounter in unrealsdk.find_all("SpawnerStyle_Encounter", exact=False)[1:]:
        for encounter in encounter.waves:    
            encounter.advancement.percent = 0
            encounter.advancement.timer = 0
            if "SpawnerStyle_Single" in str(encounter.SpawnerStyle):
                den = unrealsdk.construct_object("SpawnerStyle_Den", outer=ENGINE.Outer)
                den.SpawnOptions = encounter.SpawnerStyle.SpawnOptions
                den.bInfinite = False
                den.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value
                den.MaxAliveActorsWhenPassive.AttributeInitializationData.BaseValueScale = EnemySlider.value
                den.MaxAliveActorsWhenThreatened.AttributeInitializationData.BaseValueScale = EnemySlider.value
                encounter.SpawnerStyle = den

    for Single in unrealsdk.find_all("SpawnerComponent", exact=False)[1:]:
        if "SpawnerStyle_Single" in str(Single.SpawnerStyle):
            den = unrealsdk.construct_object("SpawnerStyle_Den", outer=ENGINE.GameViewport.World.CurrentLevel.OwningWorld)
            den.SpawnOptions = Single.SpawnerStyle.SpawnOptions
            den.bInfinite = False
            den.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value
            den.MaxAliveActorsWhenPassive.AttributeInitializationData.BaseValueScale = EnemySlider.value
            den.MaxAliveActorsWhenThreatened.AttributeInitializationData.BaseValueScale = EnemySlider.value
            Single.OverrideSpawnerStyle(den)

    for spawner in unrealsdk.find_all("Spawner", exact=False):
        spawner.ResetSpawning()
        if "HyperionSpawnAnchor" in str(spawner):
                for MaxSpawningActor in spawner.SpawnMixPossibilities:
                    MaxSpawningActor.MaxSpawningActor_11_1F69040248FDAA7AE73FD9B97D675F91 = MaxSpawningActor.MaxSpawningActor_11_1F69040248FDAA7AE73FD9B97D675F91 * EnemySlider.value

    SpawnCap.enable(), ExtraSpawnPoints.enable()


@hook("/Script/OakGame.OakSpawnerComponent:OnWaveWarmupCallback", Type.PRE)
def CartelSingleSpawns(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    if "SpawnerStyle_Single" in str(obj.SpawnerStyle):
        if obj.SpawnerStyleOverride == None :
            den = unrealsdk.construct_object("SpawnerStyle_Den", outer=ENGINE.GameViewport.World.CurrentLevel.OwningWorld)
            den.SpawnOptions = obj.SpawnerStyle.SpawnOptions
            den.bInfinite = False
            den.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value
            den.MaxAliveActorsWhenPassive.AttributeInitializationData.BaseValueScale = EnemySlider.value
            den.MaxAliveActorsWhenThreatened.AttributeInitializationData.BaseValueScale = EnemySlider.value
            den.NumAliveActorsParam.AttributeInitializationData.BaseValueConstant = EnemySlider.value
            obj.OverrideSpawnerStyle(den)

        elif obj.SpawnerStyleOverride.NumActorsParam.AttributeInitializationData.BaseValueScale != EnemySlider.value:
            obj.SpawnerStyleOverride.NumActorsParam.AttributeInitializationData.BaseValueScale = EnemySlider.value
            obj.SpawnerStyleOverride.MaxAliveActorsWhenPassive.AttributeInitializationData.BaseValueScale = EnemySlider.value
            obj.SpawnerStyleOverride.MaxAliveActorsWhenThreatened.AttributeInitializationData.BaseValueScale = EnemySlider.value

@hook("/Script/OakGame.GFxExperienceBar:extFinishedDim", Type.POST)
def SpawnCap(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    unrealsdk.find_all("SpawnManager")[-1].MaxSpawnCost = 2147483647
    unrealsdk.find_all("SpawnManager")[-1].MaxActorsSpawnedPerFrame = 2147483647

    SpawnCap.disable()

def MakeSpawnPoint(spawner: UObject, LocationList: UObject, RotationList: UObject) -> None:
    for location in LocationList:
        OakSpawnPoint = unrealsdk.construct_object("OakSpawnPoint", outer=ENGINE.GameViewport.World.CurrentLevel.OwningWorld.PersistentLevel)
        OakSpawnPoint.RootComponent.AttachChildren.append(OakSpawnPoint.SpawnPointComponent)
        OakSpawnPoint.K2_TeleportTo(location, RotationList[LocationList.index(location)])
        spawner.spawnercomponent.spawnpoints.append(OakSpawnPoint)
        if spawner.SpawnerComponent.SpawnPointUseType == 1:
            OakSpawnPoint.SpawnPointComponent.SpawnAction = spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.SpawnAction
            OakSpawnPoint.SpawnPointComponent.SpawnStretchType = spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.SpawnStretchType
            OakSpawnPoint.SpawnPointComponent.StretchyPoint = spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.StretchyPoint
        else:
            OakSpawnPoint.SpawnPointComponent.SpawnAction = spawner.SpawnPointComponent.SpawnAction
            OakSpawnPoint.SpawnPointComponent.SpawnStretchType = spawner.SpawnPointComponent.SpawnStretchType
            OakSpawnPoint.SpawnPointComponent.StretchyPoint = spawner.SpawnPointComponent.StretchyPoint
    spawner.SpawnerComponent.SpawnPointUseType = 1

def MakeSpawnOffSet(spawner: UObject, OffSet: UObject) -> None:
    OffSetAmount: list = [unrealsdk.make_struct("Vector", X=OffSet, Y=0, Z=0),unrealsdk.make_struct("Vector", X=-OffSet, Y=0, Z=0),unrealsdk.make_struct("Vector", X=0, Y=OffSet, Z=0),unrealsdk.make_struct("Vector", X=0, Y=-OffSet, Z=0),unrealsdk.make_struct("Vector", X=0, Y=0, Z=0), unrealsdk.make_struct("Vector", X=-OffSet, Y=OffSet, Z=0), unrealsdk.make_struct("Vector", X=-OffSet, Y=-OffSet, Z=0), unrealsdk.make_struct("Vector", X=OffSet, Y=-OffSet, Z=0), unrealsdk.make_struct("Vector", X=OffSet, Y=OffSet, Z=0)]
    if spawner.SpawnerComponent.SpawnPointUseType <= 1 and len(spawner.spawnercomponent.spawnpoints) <= 1:
        #print("New Spawnpoints: "+str(spawner))
        for AddOffset in OffSetAmount:
            OakSpawnPoint = unrealsdk.construct_object("OakSpawnPoint", outer=ENGINE.GameViewport.World.CurrentLevel.OwningWorld.PersistentLevel)
            OakSpawnPoint.RootComponent.AttachChildren.append(OakSpawnPoint.SpawnPointComponent)
            OakSpawnPoint.SpawnPointComponent.RelativeLocation =  AddOffset
            spawner.spawnercomponent.spawnpoints.append(OakSpawnPoint)
            if spawner.SpawnerComponent.SpawnPointUseType == 1:
                OakSpawnPoint.K2_TeleportTo(spawner.spawnercomponent.SpawnPoints[0].RootComponent.RelativeLocation, spawner.spawnercomponent.SpawnPoints[0].RootComponent.RelativeRotation)
                OakSpawnPoint.SpawnPointComponent.SpawnAction = spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.SpawnAction
                OakSpawnPoint.SpawnPointComponent.SpawnStretchType = spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.SpawnStretchType
                OakSpawnPoint.SpawnPointComponent.StretchyPoint = spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.StretchyPoint
                OakSpawnPoint.SpawnPointComponent.StretchyPoint.Translation = unrealsdk.make_struct("Vector", X=spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.StretchyPoint.Translation.x - AddOffset.x, Y=spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.StretchyPoint.Translation.y - AddOffset.y, Z=spawner.spawnercomponent.spawnpoints[0].SpawnPointComponent.StretchyPoint.Translation.z - AddOffset.z)
            else:
                OakSpawnPoint.K2_TeleportTo(spawner.spawnercomponent.RelativeLocation, spawner.spawnercomponent.RelativeRotation)
                OakSpawnPoint.SpawnPointComponent.SpawnAction = spawner.SpawnPointComponent.SpawnAction
                OakSpawnPoint.SpawnPointComponent.SpawnStretchType = spawner.SpawnPointComponent.SpawnStretchType
                OakSpawnPoint.SpawnPointComponent.StretchyPoint = spawner.SpawnPointComponent.StretchyPoint
                OakSpawnPoint.SpawnPointComponent.StretchyPoint.Translation = unrealsdk.make_struct("Vector", X=spawner.SpawnPointComponent.StretchyPoint.Translation.x - AddOffset.x, Y=spawner.SpawnPointComponent.StretchyPoint.Translation.y - AddOffset.y, Z=spawner.SpawnPointComponent.StretchyPoint.Translation.z - AddOffset.z)
        spawner.SpawnerComponent.SpawnPointUseType = 1
    elif spawner.SpawnerComponent.SpawnPointUseType == 2:
        for SpawnPointGroups in spawner.spawnercomponent.spawnpointgroups:
            if len(SpawnPointGroups.spawnpoints) == 1:
                #print("New Spawnpoints: "+str(spawner))
                for AddOffset in OffSetAmount:
                    OakSpawnPoint = unrealsdk.construct_object("OakSpawnPoint", outer=ENGINE.GameViewport.World.CurrentLevel.OwningWorld.PersistentLevel)
                    OakSpawnPoint.RootComponent.AttachChildren.append(OakSpawnPoint.SpawnPointComponent)
                    OakSpawnPoint.SpawnPointComponent.RelativeLocation =  AddOffset
                    SpawnPointGroups.spawnpoints.append(OakSpawnPoint)
                    spawner.spawnercomponent.spawnpoints.append(OakSpawnPoint)
                    OakSpawnPoint.K2_TeleportTo(SpawnPointGroups.spawnpoints[0].RootComponent.RelativeLocation, SpawnPointGroups.spawnpoints[0].RootComponent.RelativeRotation)
                    OakSpawnPoint.SpawnPointComponent.SpawnAction = SpawnPointGroups.spawnpoints[0].SpawnPointComponent.SpawnAction
                    OakSpawnPoint.SpawnPointComponent.SpawnStretchType = SpawnPointGroups.spawnpoints[0].SpawnPointComponent.SpawnStretchType
                    OakSpawnPoint.SpawnPointComponent.StretchyPoint = SpawnPointGroups.spawnpoints[0].SpawnPointComponent.StretchyPoint
                    OakSpawnPoint.SpawnPointComponent.StretchyPoint.Translation = unrealsdk.make_struct("Vector", X=SpawnPointGroups.spawnpoints[0].SpawnPointComponent.StretchyPoint.Translation.x - AddOffset.x, Y=SpawnPointGroups.spawnpoints[0].SpawnPointComponent.StretchyPoint.Translation.y - AddOffset.y, Z=SpawnPointGroups.spawnpoints[0].SpawnPointComponent.StretchyPoint.Translation.z - AddOffset.z)

@hook("/Script/Engine.AnimInstance:BlueprintInitializeAnimation", Type.POST)
def ExtraSpawnPoints(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> None:
    MediumOffest: list = ["OakMissionRareSpawner'/Game/Maps/Zone_2/Prison/Prison_Mission.Prison_Mission:PersistentLevel.OakMissionRareSpawner_Dragons'", "OakMissionSpawner'/Game/Maps/Zone_2/Prison/Prison_BossDynamic.Prison_BossDynamic:PersistentLevel.PrisonBreak_Spawner_Warden'", "OakSpawner'/Game/Maps/Zone_0/Prologue/Prologue_Dynamic.Prologue_Dynamic:PersistentLevel.OakSpawner_HuntChallenge_VarkidBadass'", "OakSpawner'/Game/Maps/Zone_0/Sacrifice/Sacrifice_Dynamic.Sacrifice_Dynamic:PersistentLevel.OakSpawner_HuntChallenge-Skrakk'"]
    LargeOffest: list = ["OakSpawner'/Game/PatchDLC/Takedown2/Maps/GuardianTakedown_Boss_Dynamic.GuardianTakedown_Boss_Dynamic:PersistentLevel.OakSpawner_Boss'","OakMissionSpawner'/Game/PatchDLC/Takedown2/Maps/GuardianTakedown_MiniBoss_Combat.GuardianTakedown_MiniBoss_Combat:PersistentLevel.Spawner_Miniboss'","OakMissionRareSpawner'/Game/Maps/Zone_3/Motorcade/Motorcade_P.Motorcade_P:PersistentLevel.OakMissionRareSpawner_1'","OakMissionSpawner'/Game/PatchDLC/Raid1/Maps/Raid/Raid_Combat.Raid_Combat:PersistentLevel.OakMissionSpawner_23'","OakMissionSpawner'/Game/Maps/Zone_3/MotorcadeInterior/MotorcadeInterior_Plot.MotorcadeInterior_Plot:PersistentLevel.OakMissionSpawner_Agonizer9k'", "OakMissionSpawner'/Game/Maps/Zone_1/CityBoss/CityBoss_Mission.CityBoss_Mission:PersistentLevel.OakMissionSpawner_RampagerBoss'", "OakMissionSpawner'/Game/Maps/Zone_1/CityBoss/CityBoss_Mission.CityBoss_Mission:PersistentLevel.OakMissionSpawner_RampagerBoss_0'", "OakMissionSpawner'/Game/Maps/ProvingGrounds/Trial8/ProvingGrounds_Trial8_Dynamic.ProvingGrounds_Trial8_Dynamic:PersistentLevel.OakMissionSpawner_Boss'", "OakMissionSpawner'/Game/Maps/Zone_2/Watership/Watership_Mission.Watership_Mission:PersistentLevel.OakMissionSpawner_BalexDino'", "OakMissionSpawner'/Game/Maps/Zone_2/Watership/Watership_Mission.Watership_Mission:PersistentLevel.GenIVIV_Runnable'", "OakMissionSpawner'/Game/Maps/Zone_2/Watership/Watership_Mission.Watership_Mission:PersistentLevel.GenIVIV_Mission'", "OakMissionSpawner'/Game/Maps/Zone_1/OrbitalPlatform/OrbitalPlatform_Boss.OrbitalPlatform_Boss:PersistentLevel.BossSpawner'"]
    BlacklistOffest: list = ["OakSpawner_Mech","OakSpawner_Mech_0","OakMissionSpawner_BreakableEridianRock", "EridianWritingSpawner_","Spawner_Aurelia","BlueprintGeneratedClass'/Game/MapSpecific/Convoy/DestructibleTower/Gameplay/BP_OakSpawner_Convoy_WatchTower_02.BP_OakSpawner_Convoy_WatchTower_02_C'"]
    if EnableSpawnPoints.value == True:
        for spawner in unrealsdk.find_all("Spawner", exact=False):
            if "EdenBoss" in str(spawner.SpawnerComponent):
                LocationList: list = [unrealsdk.make_struct("Vector", X=3849, Y=-13300, Z=1516), unrealsdk.make_struct("Vector", X=3849, Y=3000, Z=1516), unrealsdk.make_struct("Vector", X=10982, Y=-4973, Z=1516)]
                RotationList: list = [unrealsdk.make_struct("Rotator", Roll =0, Pitch=0, Yaw=90), unrealsdk.make_struct("Rotator", Roll =0, Pitch=0, Yaw=270), unrealsdk.make_struct("Rotator", Roll =0, Pitch=0, Yaw=180)]

                MakeSpawnPoint(spawner, LocationList, RotationList)

            elif "Odin" in str(spawner.SpawnerComponent):
                LocationList: list = [unrealsdk.make_struct("Vector", X=35, Y=-71732, Z=-9054), unrealsdk.make_struct("Vector", X=3266, Y=-73866, Z=-9052), unrealsdk.make_struct("Vector", X=5929, Y=-73143, Z=-9014)]
                RotationList: list = [unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0)]

                MakeSpawnPoint(spawner, LocationList, RotationList)

            elif "OakMissionSpawnerTyreenRERUN" in str(spawner.SpawnerComponent):
                LocationList: list = [unrealsdk.make_struct("Vector", X=2855, Y=-4120, Z=1084), unrealsdk.make_struct("Vector", X=933, Y=-5960, Z=1087), unrealsdk.make_struct("Vector", X=4373, Y=-6712, Z=1079), unrealsdk.make_struct("Vector", X=4236, Y=-1583, Z=1084), unrealsdk.make_struct("Vector", X=1104, Y=-2132, Z=1087)]
                RotationList: list = [unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=0)]

                MakeSpawnPoint(spawner, LocationList, RotationList)

            elif "_Ruiner_" in str(spawner.SpawnerComponent):
                LocationList: list = [unrealsdk.make_struct("Vector", X=307.77777099609375, Y=-12107.6376953125, Z=2794.4921875), unrealsdk.make_struct("Vector", X=170, Y=-18099, Z=2875), unrealsdk.make_struct("Vector", X=6307, Y=-18038, Z=2868), unrealsdk.make_struct("Vector", X=6612, Y=-11881, Z=2832)]
                RotationList: list = [unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=-50.000091552734375), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=40.000091552734375), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=130.000091552734375), unrealsdk.make_struct("Rotator", Roll=0, Pitch=0, Yaw=-140.000091552734375)]

                MakeSpawnPoint(spawner, LocationList, RotationList)

            elif str(spawner) in MediumOffest:

                MakeSpawnOffSet( spawner , 300 )

            elif str(spawner) in LargeOffest:

                MakeSpawnOffSet( spawner , 600 )

            elif "SpawnAnchor" not in str(spawner) and "Sanctuary3_" not in str(spawner) and spawner.SpawnerComponent.SpawnerStyle != None and spawner.Name not in BlacklistOffest and str(spawner.Class) not in BlacklistOffest and "Lootable" not in str(spawner) and "Spawner_Dropship" not in str(spawner) and "OakMissionSpawner'/Game/Maps/Zone_2/MarshFields/MarshFields_M_Ep12Marshfields.MarshFields_M_Ep12Marshfields:PersistentLevel.OakMissionSpawner_2'" not in str(spawner):

                MakeSpawnOffSet( spawner , 100 )

    ExtraSpawnPoints.disable()
    return 

@hook("/Game/Maps/Zone_2/WetlandsBoss/WetlandsBoss_M_EP13SiblingRivalry.WetlandsBoss_M_EP13SiblingRivalry_C:EdenArchOn", Type.PRE)
def PreventGraveWardArch(obj: UObject, args: WrappedStruct, _3: Any, _4: BoundFunction) -> type[Block] | None:
    for spawner in unrealsdk.find_all("Spawner", exact=False):
        if "EdenBoss" in str(spawner.SpawnerComponent) and spawner.Spawnercomponent.GetNumAliveActors(False, False) != 0:
            return Block

@keybind("Kill All Spawns")
def Kill_spawns() -> None:
    is_hostile = get_pc().GetTeamComponent().IsHostile
    for pawn in unrealsdk.find_all("OakCharacter", exact=False):
        if not is_hostile(pawn):
            continue
        damage_comp = pawn.DamageComponent
        damage_comp.SetCurrentShield(0)
        damage_comp.SetCurrentHealth(0)
    show_hud_message("Kill All Spawns", ("All Spawns Killed"))

build_mod()