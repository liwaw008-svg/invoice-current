from conftest import CONTRACT
U=['https://invoice.example/i7','https://delivery.example/i7','https://debtor.example/policy']
def mocks(v):
 v.strict_mocks=True;v.check_pickling=True;v.mock_web(r'invoice\.example',{'status':200,'body':'Invoice I7 amount 5000 debtor Atlas.'});v.mock_web(r'delivery\.example',{'status':200,'body':'Delivery for I7 accepted.'});v.mock_web(r'debtor\.example',{'status':200,'body':'Atlas policy allows invoice I7.'});v.mock_llm(r'.*Assess eligibility.*','{"decision":"ELIGIBLE","risk_codes":[]}');v.mock_llm(r'.*Verify exact eligibility.*','{"valid":true}')
def test_lifecycle(direct_vm,direct_deploy):
 direct_vm.warp('2030-01-01T00:00:00+00:00');c=direct_deploy(CONTRACT);mocks(direct_vm);c.file('I7','Atlas',5000,U,1893463200);c.assess('I7');c.settle('I7');assert c.get_invoice('I7')['state']=='SETTLED'
def test_expiry_sources(direct_vm,direct_deploy):
 direct_vm.warp('2030-01-01T00:00:00+00:00');c=direct_deploy(CONTRACT);c.file('A','Atlas',1,U,1893456060)
 with direct_vm.expect_revert('duplicate'):c.file(' a ','Atlas',1,U,1893456060)
 with direct_vm.expect_revert('three-party'):c.file('B','Atlas',1,[U[0],U[0],U[2]],1893456060)
 direct_vm.warp('2030-01-01T00:02:00+00:00');c.expire('A');assert c.get_invoice('A')['state']=='EXPIRED'
def test_forged(direct_vm,direct_deploy):
 direct_vm.warp('2030-01-01T00:00:00+00:00');c=direct_deploy(CONTRACT);mocks(direct_vm);c.file('X','Atlas',5000,U,1893463200);x=c._review(c.invoices['X']);assert direct_vm.run_validator(leader_result=x);x=dict(x);x['digests']=x['digests'][::-1];assert not direct_vm.run_validator(leader_result=x)
