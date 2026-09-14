"""Fetch an exact completed same-repository CI artifact; never print credentials."""
from pathlib import Path
import hashlib,json,os,urllib.request,urllib.parse,zipfile,io

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if urllib.parse.urlsplit(req.full_url).hostname!=urllib.parse.urlsplit(newurl).hostname:
            redirected.remove_header('Authorization')
        return redirected

def main():
    url='https://api.github.com/repos/phatnbt/HealthInfo_UIT/actions/artifacts/10362614857/zip'
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','User-Agent':'HealthInfo-UIT-verified-repair'})
    with urllib.request.build_opener(SafeRedirect()).open(request,timeout=60) as response:data=response.read()
    assert hashlib.sha256(data).hexdigest()=='60ec6c302d535839af25d92426761dbfe3be30f6e6ac4aa75783300894345c04'
    out=Path('repair/linux_verified');out.mkdir(parents=True,exist_ok=True)
    (out/'linux_mi_aggregate_evidence.zip').write_bytes(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        summary=json.loads(z.read('repair_validation_summary.json'))
    assert summary['historical_all_models_passed'] and summary['artifact_integrity']=='PASS'
    (out/'repair_validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('PASS: recovered the exact verified132-fit Linux artifact; all historical models reproduce.')

if __name__=='__main__':main()
