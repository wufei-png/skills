// CUA browser adapter: UI operations only; no direct generation API calls.
// Caller supplies the authenticated CUA Tab. prepare() NEVER clicks Create.
export function assertPackage(p) {
  if (p.mode !== 'custom' || p.model !== 'v6' || !['Auto','Custom'].includes(p.durationMode)) throw Error('Unsupported package mode/model/duration');
  if (p.durationMode === 'Custom' && (!Number.isInteger(p.durationSeconds) || p.durationSeconds < 1)) throw Error('Explicit custom duration seconds required');
  if (p.durationMode === 'Auto' && ![undefined,null,0].includes(p.durationSeconds)) throw Error('Auto duration cannot request seconds');
  if (typeof p.instrumental !== 'boolean' || p.instrumental !== !p.lyrics.trim()) throw Error('Instrumental/lyrics mismatch');
  if (p.instrumental ? p.vocalGender !== null : !['Male','Female'].includes(p.vocalGender)) throw Error('Explicit vocal gender required; instrumental must use null');
  if (typeof p.maxMode !== 'boolean' || p.variety !== 0 || p.personalize !== false) throw Error('Explicit Max/Variety/Personalize required');
  for (const k of ['weirdnessPercent','styleInfluencePercent']) if (!Number.isInteger(p[k]) || p[k]<0 || p[k]>100) throw Error('Invalid '+k);
  for (const [k,n] of [['lyrics',5000],['styles',1000],['exclusions',1000],['title',80]]) if (typeof p[k]!=='string' || p[k].length>n) throw Error('Invalid '+k);
  if (!p.title || !p.styles || p.workspace!=='My Workspace') throw Error('Title, styles and workspace are required');
  for (const k of ['audioReference','audioInfluence','voice','persona','inspo','customModel','extend']) if (p[k]!==null) throw Error('Unsupported reference field '+k);
}
export function assertReadback(p,s) {
  assertPackage(p);
  for (const k of ['title','lyrics','styles','exclusions','vocalGender','maxMode','variety','personalize','weirdnessPercent','styleInfluencePercent','durationMode','model','workspace','instrumental']) if(s[k]!==p[k]) throw Error('Readback mismatch '+k);
  if (p.durationMode === 'Custom' && s.durationSeconds !== p.durationSeconds) throw Error('Readback mismatch durationSeconds');
  if (p.durationMode === 'Auto' && ![undefined,null,0].includes(s.durationSeconds)) throw Error('Readback mismatch unexpected fixed duration');
  if (s.mode!=='Advanced' || !s.createEnabled || !s.emptyReferenceControls) throw Error('Form mode, reference state or Create is not verified');
  return true;
}
export async function replaceLyrics(editor,text) {
  await editor.press('Meta+A');
  await editor.press('Backspace');
  if(text)await editor.fill(text);
}
export function cuaForm(tab) {
  const pw=tab.playwright;
  const exposed=l=>l.filter({visible:true}).and(pw.locator(':not([aria-hidden="true"]):not([aria-hidden="true"] *)'));
  const unique=async l=>{const v=exposed(l);await v.waitFor({state:'visible'});if(await v.count()!==1)throw Error('Missing/ambiguous live control');return v;};
  const group=label=>exposed(pw.locator('div.css-gwrmef').filter({has:pw.getByText(label,{exact:true})}));
  async function selected(label) {
    const rows=await group(label).evaluateAll(es=>es.map(e=>Array.from(e.querySelectorAll('button')).filter(b=>b.textContent!=='My Taste').map(b=>({text:b.textContent,selected:b.getAttribute('data-selected'),className:b.className,pressed:b.getAttribute('aria-pressed')}))));
    if(rows.length!==1)throw Error('Missing/ambiguous choice '+label);
    const active=[];
    for(const b of rows[0]) {
      let on=b.pressed ?? b.selected;
      if(on===null) {
        if(b.className.includes('hxc-btn-variant-standard-legacy'))on='true';
        else if(b.className.includes('hxc-btn-variant-tertiary-legacy')&&b.className.includes('text-gray-400'))on='false';
        else throw Error('Unreadable '+label+' selected state');
      }
      if(on==='true')active.push(b.text);
    }
    if(active.length>1)throw Error('Multiple selected '+label);
    return active[0]??null;
  }
  async function choice(label,target) {
    const before=await selected(label);
    if(before!==target)await (await unique(group(label).getByRole('button',{name:target??before,exact:true}))).click();
    if(await selected(label)!==target)throw Error('Choice did not read back '+label);
  }
  async function slider(name,target,max) {
    const l=await unique(pw.getByRole('slider',{name,exact:true}));
    const num=async attr=>{const v=await l.getAttribute(attr);if(v===null||!/^\d+$/.test(v))throw Error('Unreadable slider '+name);return Number(v);};
    if(await num('aria-valuemin')!==0||await num('aria-valuemax')!==max)throw Error('Changed slider scale '+name);
    const before=await num('aria-valuenow');
    for(let j=0;j<Math.abs(target-before);j++)await l.press(target>before?'ArrowRight':'ArrowLeft');
    if(await num('aria-valuenow')!==target)throw Error('Slider readback '+name);
  }
  async function readDuration() {
    const inputs=pw.locator('input[aria-label="Duration"]').filter({visible:true});
    const sliders=pw.getByRole('slider',{name:'Duration',exact:true}).filter({visible:true});
    if(await inputs.count()===0 && await sliders.count()===0) {
      if(await selected('Duration')!=='Auto')throw Error('Auto duration is not selected');
      return {durationMode:'Auto',durationSeconds:0};
    }
    const input=await unique(inputs),control=await unique(sliders);
    const display=await input.evaluate(e=>e.value);
    const match=/^(\d+):([0-5]\d)$/.exec(display);
    if(!match)throw Error('Unreadable duration display');
    const values={};for(const attr of ['aria-valuenow','aria-valuemin','aria-valuemax']) {
      const value=await control.getAttribute(attr);
      if(value===null||!/^\d+$/.test(value))throw Error('Unreadable duration slider');
      values[attr]=Number(value);
    }
    const seconds=Number(match[1])*60+Number(match[2]);
    if(seconds!==values['aria-valuenow']||await selected('Duration')==='Auto')throw Error('Duration controls disagree');
    return {durationMode:'Custom',durationSeconds:seconds,durationMin:values['aria-valuemin'],durationMax:values['aria-valuemax']};
  }
  async function setDuration(p) {
    if(p.durationMode==='Auto') {
      if((await readDuration()).durationMode!=='Auto') {
        const auto=group('Duration').getByRole('button',{name:'Auto',exact:true});
        if(await auto.count()===1)await auto.click();
        else {
          // Current Custom UI replaces both choices with a Duration-only reset icon.
          // Its return to the official Auto selection was verified on 2026-10-11.
          await (await unique(group('Duration').locator('svg.cursor-pointer[data-base-ui-tooltip-trigger]'))).click();
        }
      }
    } else {
      if((await readDuration()).durationMode!=='Custom')await (await unique(group('Duration').getByRole('button',{name:'Custom',exact:true}))).click();
      const input=await unique(pw.locator('input[aria-label="Duration"]'));
      const before=await readDuration();
      if(p.durationSeconds<before.durationMin||p.durationSeconds>before.durationMax)throw Error('Requested duration outside live range');
      await input.fill(Math.floor(p.durationSeconds/60)+':'+String(p.durationSeconds%60).padStart(2,'0'));
      await input.press('Tab');
    }
    const after=await readDuration();
    if(after.durationMode!==p.durationMode||(p.durationMode==='Custom'&&after.durationSeconds!==p.durationSeconds))throw Error('Duration did not read back');
  }
  async function read() {
    const value=async l=>(await unique(l)).evaluate(e=>e.value);
    const lyrics=await (await unique(pw.getByRole('textbox',{name:'Lyrics editor',exact:true}))).evaluate(e=>Array.from(e.children).map(p=>p.textContent).join('\n'));
    const sliders={};for(const name of ['Weirdness','Style Influence','Variety'])sliders[name]=await (await unique(pw.getByRole('slider',{name,exact:true}))).getAttribute('aria-valuenow');
    const values={title:await value(pw.getByRole('textbox',{name:'Song Title (Optional)',exact:true})),lyrics,styles:await value(pw.locator('textarea[maxlength="1000"]')),exclusions:await value(pw.getByRole('textbox',{name:'Exclude styles',exact:true})),sliders,
      mode:await (await unique(pw.getByRole('tab',{name:'Advanced',exact:true}).and(pw.locator('[aria-selected="true"]')))).innerText(),creditsLabel:await (await unique(pw.getByRole('button',{name:/^Credits remaining:/}))).getAttribute('aria-label')};
    for(const v of Object.values(values.sliders))if(v===null||!/^\d+$/.test(v))throw Error('Unreadable slider');
    const refs=['Add audio - Browse, upload, or record audio','Add Voice','Add inspiration from a playlist'];
    let emptyReferenceControls=true;for(const name of refs)if(await pw.getByRole('button',{name,exact:true}).filter({visible:true}).count()!==1)emptyReferenceControls=false;
    const maxChoice=await selected('Max Mode'),personalizeChoice=await selected('Personalize');
    if(!['On','Off'].includes(maxChoice)||!['On','Off'].includes(personalizeChoice))throw Error('Unreadable Max/Personalize');
    return {...values,weirdnessPercent:Number(values.sliders.Weirdness),styleInfluencePercent:Number(values.sliders['Style Influence']),variety:Number(values.sliders.Variety),
      instrumental:!values.lyrics.trim(),vocalGender:await selected('Vocal Gender'),...await readDuration(),maxMode:maxChoice==='On',personalize:personalizeChoice==='On',
      model:await pw.getByRole('button',{name:'v6',exact:true}).innerText(),workspace:await pw.getByRole('button',{name:'My Workspace',exact:true}).innerText(),
      createEnabled:await pw.getByRole('button',{name:'Create song',exact:true}).isEnabled(),emptyReferenceControls};
  }
  async function prepare(p) {
    assertPackage(p);
    const advanced=await unique(pw.getByRole('tab',{name:'Advanced',exact:true}));
    if(await advanced.getAttribute('aria-selected')!=='true')await advanced.click();
    const more=await unique(pw.getByRole('button',{name:/^More Options/}));
    if(await more.getAttribute('aria-expanded')!=='true')await more.click();
    await (await unique(group('Duration'))).waitFor({state:'visible'});
    if(await pw.getByRole('button',{name:'v6',exact:true}).count()!==1)throw Error('Requested v6 is not selected');
    await replaceLyrics(await unique(pw.getByRole('textbox',{name:'Lyrics editor',exact:true})),p.lyrics);
    await (await unique(pw.locator('textarea[maxlength="1000"]'))).fill(p.styles);
    await (await unique(pw.getByRole('textbox',{name:'Exclude styles',exact:true}))).fill(p.exclusions);
    await (await unique(pw.getByRole('textbox',{name:'Song Title (Optional)',exact:true}))).fill(p.title);
    await choice('Vocal Gender',p.vocalGender);await setDuration(p);await choice('Max Mode',p.maxMode?'On':'Off');
    await slider('Weirdness',p.weirdnessPercent,100);await slider('Style Influence',p.styleInfluencePercent,100);await slider('Variety',p.variety,4);await choice('Personalize','Off');
    const result=await read();assertReadback(p,result);return result;
  }
  return {prepare,read,selected};
}
