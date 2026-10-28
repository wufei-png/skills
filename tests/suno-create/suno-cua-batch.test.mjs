import test from 'node:test';
import assert from 'node:assert/strict';
import {assertPackage,assertReadback,replaceLyrics,cuaForm} from '../../skills/creative/suno-create/scripts/suno-cua-batch.mjs';
import {fakeCua} from './fake-cua.mjs';
const p={mode:'custom',model:'v6',durationMode:'Auto',instrumental:false,vocalGender:'Female',maxMode:true,variety:0,personalize:false,weirdnessPercent:35,styleInfluencePercent:82,title:'Example',lyrics:'[Verse]\nA line',styles:'Acoustic soul',exclusions:'rap',workspace:'My Workspace',audioReference:null,audioInfluence:null,voice:null,persona:null,inspo:null,customModel:null,extend:null};
const s={...p,mode:'Advanced',createEnabled:true,emptyReferenceControls:true};
test('rejects stale settings individually before spending',()=>{for(const [key,value] of Object.entries({lyrics:'previous song',styles:'old styles',exclusions:'',vocalGender:'Male',maxMode:false,variety:1,personalize:true,weirdnessPercent:50,styleInfluencePercent:50,durationMode:'Custom',model:'v6-wild',workspace:'Other',instrumental:true}))assert.throws(()=>assertReadback(p,{...s,[key]:value}),/Readback mismatch/);});
test('requires all explicit no-reference declarations',()=>{for(const k of ['audioReference','audioInfluence','voice','persona','inspo','customModel','extend'])assert.throws(()=>assertPackage({...p,[k]:undefined}),/reference/);});
test('instrumental cannot inherit vocal gender or lyrics',()=>{const i={...p,instrumental:true,lyrics:'',vocalGender:null};assert.doesNotThrow(()=>assertPackage(i));assert.throws(()=>assertPackage({...i,vocalGender:'Female'}),/gender/);assert.throws(()=>assertPackage({...i,lyrics:'stale vocal'}),/mismatch/);});
test('lexical empty fill cannot silently keep previous song',async()=>{let content='previous lyric',calls=[];const editor={async press(key){calls.push(key);if(key==='Backspace')content='';},async fill(value){calls.push('fill');if(value)content=value;}};await replaceLyrics(editor,'');assert.equal(content,'');assert.deepEqual(calls,['Meta+A','Backspace']);await replaceLyrics(editor,'new\nlines');assert.equal(content,'new\nlines');});
test('rejects disabled Create or unverified reference area',()=>{assert.throws(()=>assertReadback(p,{...s,createEnabled:false}));assert.throws(()=>assertReadback(p,{...s,emptyReferenceControls:false}));assert.equal(assertReadback(p,s),true);});
test('fixed duration must be explicit and read back exactly before spending',()=>{
  const custom={...p,durationMode:'Custom',durationSeconds:205};
  assert.doesNotThrow(()=>assertPackage(custom));
  assert.throws(()=>assertPackage({...custom,durationSeconds:undefined}),/seconds/);
  assert.throws(()=>assertPackage({...custom,durationSeconds:205.5}),/seconds/);
  assert.throws(()=>assertPackage({...p,durationSeconds:205}),/Auto duration/);
  assert.throws(()=>assertReadback(custom,{...s,durationMode:'Custom',durationSeconds:200}),/durationSeconds/);
  assert.equal(assertReadback(custom,{...s,durationMode:'Custom',durationSeconds:205}),true);
  assert.throws(()=>assertReadback(p,{...s,durationSeconds:205}),/fixed duration/);
});
test('prepares a custom duration and resets to Auto without submitting',async()=>{
  const {tab,state}=fakeCua(),form=cuaForm(tab);
  const custom=await form.prepare({...p,durationMode:'Custom',durationSeconds:205});
  assert.equal(custom.durationSeconds,205);
  const auto=await form.prepare(p);
  assert.equal(auto.durationMode,'Auto');
  assert.equal(state.createClicks,0);
});
test('refuses inconsistent custom duration controls without submitting',async()=>{
  const {tab,state}=fakeCua();state.durationMismatch=true;
  await assert.rejects(cuaForm(tab).prepare({...p,durationMode:'Custom',durationSeconds:205}),/Duration controls disagree/);
  assert.equal(state.createClicks,0);
});
