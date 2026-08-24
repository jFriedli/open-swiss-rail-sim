export const ROUTE_PACKAGE_SCHEMA_VERSION=1;

export type RouteAssetKey='route'|'terrain'|'scenery'|'landscape'|'journey'|'railNetwork'|'traffic';
export type RoutePackage={
  schemaVersion:number;
  id:string;
  name:string;
  description:string;
  supportTier:'FULL'|'PARTIAL'|'UNSUPPORTED';
  sourceDate:string;
  localOriginLv95:{easting:number;northing:number;elevation:number};
  boundsLv95:{minEasting:number;maxEasting:number;minNorthing:number;maxNorthing:number};
  routeLengthM:number;
  playerService:{name:string;tripId:string;serviceDate:string};
  assets:Record<RouteAssetKey,string>;
  capabilities:{standardGauge:boolean;adhesion:boolean;conventionalSignals:boolean;etcsL2:boolean;rack:boolean;tram:boolean};
  coverage:{mappedSignals:number;scenarioSignals:number;speedLimit:number;platformMatching:number};
  sources:Record<string,{classification:'REAL'|'OPEN_MAPPING'|'DERIVED'|'SIMULATED';dataset:string;date?:string}>;
  testCheckpoints:{id:string;s:number;kind:string}[];
  packageBytes:number;
};
export type RouteCatalog={schemaVersion:number;routes:Array<Pick<RoutePackage,'id'|'name'|'description'|'supportTier'|'routeLengthM'|'playerService'|'coverage'|'packageBytes'>>};

export function validateRoutePackage(value:RoutePackage){
  if(value.schemaVersion!==ROUTE_PACKAGE_SCHEMA_VERSION)throw Error(`Unsupported RoutePackage schema ${value.schemaVersion}; runtime supports ${ROUTE_PACKAGE_SCHEMA_VERSION}`);
  if(!/^[a-z0-9-]+$/.test(value.id))throw Error('Invalid RoutePackage id');
  if(!Number.isFinite(value.routeLengthM)||value.routeLengthM<=0)throw Error('Invalid RoutePackage length');
  for(const key of ['route','terrain','scenery','landscape','journey','railNetwork','traffic'] as RouteAssetKey[])if(!value.assets[key])throw Error(`RoutePackage missing ${key}`);
  if(value.capabilities.rack||value.capabilities.tram||!value.capabilities.standardGauge||!value.capabilities.adhesion)throw Error(`${value.name} is unsupported by the current standard-gauge adhesion runtime`);
  return true;
}
