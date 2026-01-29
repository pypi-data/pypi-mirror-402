import typing

SERVICE_SPECS: typing.Mapping[str, list[str]] = {
    'netmonitor': [
        'https://docs.oracle.com/en-us/iaas/api/specs/8af785f2fcabba899f4f05867f7d2cb38cc822b3b1658fecd6e9a5db669bc30c.yaml'
    ],
    'ocb': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c321f3149c29b4ca6e4030a39208852a1148785c372d569ef4b147e313ee18a3.yaml'
    ],
    'access-governance-cp': [
        'https://docs.oracle.com/en-us/iaas/api/specs/a5cdce2cc56dddfbf507db56ef7e68c5117ef46ee84978f4fec55266d58aa370.yaml'
    ],
    'adm': [
        'https://docs.oracle.com/en-us/iaas/api/specs/460bba86e8b85a4a4c35b2abd0907fd9dd891de1a65c1e7e418741eaa8db5ea6.yaml'
    ],
    'advisor': [
        'https://docs.oracle.com/en-us/iaas/api/specs/321b6e72c522371194cdfccd7f4baba8c0059033e00f99013ea466ec44921ca3.yaml'
    ],
    'ai-data-platform': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1d0e9438d203a3d74bcb4389030d7179855358c44dbd41f8fa9ca8ae5638bb7f.yaml'
    ],
    'analytics': [
        'https://docs.oracle.com/en-us/iaas/api/specs/9bcc53a4edfb39ed432d422fd992444b637d99197bac3f5aedeb0d97eb42188a.yaml'
    ],
    'announcements': [
        'https://docs.oracle.com/en-us/iaas/api/specs/ad81e510c25e589a2fdfbfe0fb957253a658175b2922b7951ddb17b4910c849b.yaml'
    ],
    'api-gateway': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c9572dd2652e53a2c389b502d61b5d6ac097ed1b014b4ca10ea9e4791d8b3e3d.yaml'
    ],
    'apm-config': [
        'https://docs.oracle.com/en-us/iaas/api/specs/42166576f1e5ff54f09f5720889809a704216efb7c095b6116285a45b2ad2b6f.yaml'
    ],
    'apm-control-plane': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c9b42c2f3d5dc4b7c4feb3f85ad0efa2fe29fe3e3cbbb4f825dd15af9bbbb959.yaml'
    ],
    'apm-synthetic-monitoring': [
        'https://docs.oracle.com/en-us/iaas/api/specs/202b308f03ee919108f01637e7dfa3ef4f65f73c616827e1c347451589608915.yaml'
    ],
    'apm-trace-explorer': [
        'https://docs.oracle.com/en-us/iaas/api/specs/d1cc8021a03784e751fe54c779074681c153f47a8bd2975f098d6c8988748126.yaml'
    ],
    'audit': [
        'https://docs.oracle.com/en-us/iaas/api/specs/a92c1b8661432d4112968ecbe805522122f66f9e5afabe9e1e072ef9ddf3a674.yaml'
    ],
    'autoscaling': [
        'https://docs.oracle.com/en-us/iaas/api/specs/413902c2f198bba0a2c9aad62a4454040fa6d057036747336477142eadcf1214.yaml'
    ],
    'bastion': [
        'https://docs.oracle.com/en-us/iaas/api/specs/31acb88061f5176111beb8e181c6dad2beb5f2f17de5a04802c4aedb4e37219c.yaml'
    ],
    'batch': [
        'https://docs.oracle.com/en-us/iaas/api/specs/42c277d25c3799564b412ef83393cb66a327b0bd63b05c63ec03362935176621.yaml'
    ],
    'bigdata': [
        'https://docs.oracle.com/en-us/iaas/api/specs/52768dd277632eef940b901896db4c9a78a59b50bde328cb447fe70a3f17f14c.yaml'
    ],
    'blockchain': [
        'https://docs.oracle.com/en-us/iaas/api/specs/37c144ccf52c32d759221783a2a5c9327cc3be13ed5730d8079ce8ef11e33add.yaml'
    ],
    'budgets': [
        'https://docs.oracle.com/en-us/iaas/api/specs/5206052d079d5c8ca6b161abffcdbcb07a30a59e95bc818bd6f4e9f87c304d17.yaml'
    ],
    'certificates': [
        'https://docs.oracle.com/en-us/iaas/api/specs/61256b964ce395d6570b1ae52107166759c8a0bf10a51bf6d5072f009382dfc6.yaml'
    ],
    'certificatesmgmt': [
        'https://docs.oracle.com/en-us/iaas/api/specs/80425b21aa2e3fad185996feb49aed3bd0f37451c410f8b7991dad60f8140f00.yaml'
    ],
    'cloud-guard': [
        'https://docs.oracle.com/en-us/iaas/api/specs/0e13d9eaa80694b2ef028102ebc10ddb5f6d4386b62eae929a36580811f17528.yaml'
    ],
    'clusterplacementgroups': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1555b5fb3c43d0a4f1fbdb999be3e1332280461b2a0100d3104ec825424a1cbc.yaml'
    ],
    'compute-cloud-at-customer': [
        'https://docs.oracle.com/en-us/iaas/api/specs/468775184ca4fe31235420733267b83b5fc48f58050a9529483039f6b2d4630c.yaml'
    ],
    'container-instances': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1dce90c529448f9df940116cc4dcb7d1512d40d743a25f805d0adcaa7169efc2.yaml'
    ],
    'containerengine': [
        'https://docs.oracle.com/en-us/iaas/api/specs/822a3af31f35900b8aaa45c012f28c9722aaf7b799d094a8a8d64aed7b1afadd.yaml'
    ],
    'dashboard': [
        'https://docs.oracle.com/en-us/iaas/api/specs/58e0456bca86b42263bb0bdaa4ccd27ef1ac92ff5f920f5850ee1b12cb4bd0a0.yaml'
    ],
    'data-catalog': [
        'https://docs.oracle.com/en-us/iaas/api/specs/7618ae72fe643f802561e1bdc0305cdce2a8f163cceb45f87aac32a72b72e546.yaml'
    ],
    'data-flow': [
        'https://docs.oracle.com/en-us/iaas/api/specs/073c6ddbe388e3bb7984f9c13c7172166cb5a1063c9e2251c3c7dd3f7d49bd2e.yaml'
    ],
    'data-integration': [
        'https://docs.oracle.com/en-us/iaas/api/specs/85979cfb4fad4fd1086a187bef6767b32619ed61ae3506aad96bd6431326aa45.yaml'
    ],
    'data-safe': [
        'https://docs.oracle.com/en-us/iaas/api/specs/e5b28aa1cbfc2d1b67bc3f7b3e045d1aa040d9f5bb966f8862b812304b730a7c.yaml'
    ],
    'data-science': [
        'https://docs.oracle.com/en-us/iaas/api/specs/f364519c5d3588895d7f92794fc0feadcc08c666088062eb90a324b7fb2bf22f.yaml'
    ],
    'database': [
        'https://docs.oracle.com/en-us/iaas/api/specs/21e20cba32cd7fb621ed5bcfe969eb5808d5db1644b4511fc1600e6e4ba0ff8f.yaml'
    ],
    'database-management': [
        'https://docs.oracle.com/en-us/iaas/api/specs/78f8e3c6e94b42e129280c81915159f518030fcd251a66d46be28502b956c77e.yaml'
    ],
    'database-migration': [
        'https://docs.oracle.com/en-us/iaas/api/specs/d9747496b24a62b2bad1e4a1025515fd9832a9d1cb547e50df210d415aaccd77.yaml',
        'https://docs.oracle.com/en-us/iaas/api/specs/68baab093072ef67333dfcf16d85ed55fbc21d726a4d808b4ce36e0a99d2f034.yaml',
        'https://docs.oracle.com/en-us/iaas/api/specs/a0c1aa5b941d15b4e1f2dcf9a438e9c939dd232dababcac7ff8bc42fdf66177d.yaml',
    ],
    'database-multicloud-integrations': [
        'https://docs.oracle.com/en-us/iaas/api/specs/b398f2790470f12a4dcaccc323c3132e369cf6fedb45199c41f6e66c8c49e6d8.yaml'
    ],
    'database-tools': [
        'https://docs.oracle.com/en-us/iaas/api/specs/8f1cffff79077422a7037a9b6759a3184b5aa7b123f2ac592b5d67a44786f696.yaml'
    ],
    'datalabeling': [
        'https://docs.oracle.com/en-us/iaas/api/specs/a595c62dbbef0595235745dd826e59437d410e04914007447c8d6414cabfd57b.yaml'
    ],
    'datalabeling-dp': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1392e537ef1367fd9356a9545e4dc5a6053ea0441d31c576d53322e1c864e260.yaml'
    ],
    'delegate-access-control': [
        'https://docs.oracle.com/en-us/iaas/api/specs/a8a2c21c4173be02e12261ac766b55eea1f176c7edf194b4f291fcfd45e75529.yaml'
    ],
    'devops': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1d632ce78020a0d7fa6c8161bdef77b8ef9d426c524acb2c80e580ff02d26b5c.yaml'
    ],
    'digital-assistant': [
        'https://docs.oracle.com/en-us/iaas/api/specs/531121eb7dd0c8b1b4e7a3fffd325b5661fa61d805d6ebcfadb6ba7b0aa8d43b.yaml'
    ],
    'disaster-recovery': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1ded494ac548eb031485a9ea3998c83e08ab0923e3ac8e6afa8a6e890fc34c21.yaml'
    ],
    'dms': [
        'https://docs.oracle.com/en-us/iaas/api/specs/fb3f87892acfebb2d30cddd4ec628119125fc820d1c3fad363bf9d5ed5497dc9.yaml'
    ],
    'dns': [
        'https://docs.oracle.com/en-us/iaas/api/specs/cf00051a86cb5e953d7a660191e10bbfb22a8ea0ef2c9a79ad5ded5dd4dcc7f1.yaml'
    ],
    'document-understanding': [
        'https://docs.oracle.com/en-us/iaas/api/specs/4131808fd66c893ddb009ad5c727048fe81e9aa7a2cf208257100cad4a7846a0.yaml'
    ],
    'edsfu': [
        'https://docs.oracle.com/en-us/iaas/api/specs/39875469b972aaeeddc506c447e38701c4b3127c71f3e5eea2aea25dae4ab55e.yaml'
    ],
    'emaildelivery': [
        'https://docs.oracle.com/en-us/iaas/api/specs/9467c30d639b82df667ec52240b02c680cc13f4c754277a576c8fcb2862d5dd1.yaml'
    ],
    'emaildeliverysubmission': [
        'https://docs.oracle.com/en-us/iaas/api/specs/4e3a56bac2b61ee8cac57b79e304d7ea39b7d9d7a505e3b06e38116ff0b5f8e8.yaml'
    ],
    'events': [
        'https://docs.oracle.com/en-us/iaas/api/specs/589e549735dd190d78e8fb6ff9891048de06687f3bb47308774991e267d754a9.yaml'
    ],
    'filestorage': [
        'https://docs.oracle.com/en-us/iaas/api/specs/2b79229ae8b5661b2e35d1a8332b3b7a8d1ebf40b13a22215416ca3033e547bf.yaml'
    ],
    'fleet-management': [
        'https://docs.oracle.com/en-us/iaas/api/specs/f2a4dee9662380ab95fd5614b5146056386c5395b67754e87137de7f895d5604.yaml'
    ],
    'functions': [
        'https://docs.oracle.com/en-us/iaas/api/specs/871ec453f0e507fb952397da2734bb642ed1aa47aeb893592d5a05a47b429f37.yaml'
    ],
    'functionsdocgenpbf': [
        'https://docs.oracle.com/en-us/iaas/api/specs/2759931116bb04dc62de76027c85704524479cd94fcd8b9dffc6f9713fba1481.yaml'
    ],
    'fusion-applications': [
        'https://docs.oracle.com/en-us/iaas/api/specs/ce292724a3ca1f17a729a7357bb42eb08323608c5e3d049439aa69951ab15c74.yaml'
    ],
    'generative-ai': [
        'https://docs.oracle.com/en-us/iaas/api/specs/6c963cb7fc2f5a89905da2be8df5ba505e35726d53c6be2f3905b8a3e20a429b.yaml'
    ],
    'generative-ai-agents': [
        'https://docs.oracle.com/en-us/iaas/api/specs/a3e6be1761000d2b7965b4a1545462e4b052228afe386bd71a47ee7b991b838f.yaml'
    ],
    'generative-ai-agents-client': [
        'https://docs.oracle.com/en-us/iaas/api/specs/ba09f03f08f2b0345c4baef2a703aa81de4e14644d29899488bf8f059e459a38.yaml'
    ],
    'generative-ai-inference': [
        'https://docs.oracle.com/en-us/iaas/api/specs/20efb8d6b460fe195e91a8bdf9631c61ba16ef13f198e9f67d3af9a938ad66e7.yaml'
    ],
    'generic': [
        'https://docs.oracle.com/en-us/iaas/api/specs/971715d2904d72ed7469c3053f482634a9aea37a123cf4d26b223b68896898e0.yaml'
    ],
    'globally-distributed-database': [
        'https://docs.oracle.com/en-us/iaas/api/specs/83d38468890cd01e7afd5d83bf08b43578b3611d1c707d79ef505c37e85c9138.yaml'
    ],
    'goldengate': [
        'https://docs.oracle.com/en-us/iaas/api/specs/86b1e65d103b1a04757b911deaff568f94ccef102096d75f59c766456dd475c5.yaml'
    ],
    'healthchecks': [
        'https://docs.oracle.com/en-us/iaas/api/specs/7bd7df629d66a3b89f83c170e1f4378b5baca11c3cb832176fabf4a99e48ed91.yaml'
    ],
    'iaas': [
        'https://docs.oracle.com/en-us/iaas/api/specs/10c29707147c910c242e64e4ce0b157ef9201a40c97e4cbfb77410be46360479.yaml'
    ],
    'identity': [
        'https://docs.oracle.com/en-us/iaas/api/specs/aa2041df364a338d46d8bd1a995c2aaec86bfb1ad1963cc90d787f54bfda97f5.yaml'
    ],
    'identity-domains': [
        'https://docs.oracle.com/en-us/iaas/api/specs/ba3bfd439325eb31153a9c7a2fe1b54257a79082f61ef86d9f9de998bfde084c.yaml'
    ],
    'identity-dp': [
        'https://docs.oracle.com/en-us/iaas/api/specs/7e3c983ab04cba050355f42f4af4739877daa289937575a7498b525ccb4a29f4.yaml'
    ],
    'incidentmanagement': [
        'https://docs.oracle.com/en-us/iaas/api/specs/0abf97e0c0fdcc7c80e4fc32e20fc9bdd7a9946d4d98c39eefe823bac155c0c4.yaml'
    ],
    'instanceagent': [
        'https://docs.oracle.com/en-us/iaas/api/specs/abc54d26544daece6d8f5d23598a268c1ec36b55d8481463fac336c5329097b9.yaml'
    ],
    'integration': [
        'https://docs.oracle.com/en-us/iaas/api/specs/656279256ccceb8f710453cb4694312ddd60c490c5ef0b7c282dc4be9bcb8eca.yaml'
    ],
    'iot': [
        'https://docs.oracle.com/en-us/iaas/api/specs/5835117dba522a3f75ca501db67eefdcd18af62891b5e605156cf6841c7bc64f.yaml'
    ],
    'itas': [
        'https://docs.oracle.com/en-us/iaas/api/specs/2fd4343e03912de02e1b6e82eb9fed428530a4191aff1e43fb986fb90c429748.json'
    ],
    'jms': [
        'https://docs.oracle.com/en-us/iaas/api/specs/756c07623c433632650cfadcb9ae28431b4fdfcf0d7def89e16cd697ac3d44a2.yaml'
    ],
    'jms-java-download': [
        'https://docs.oracle.com/en-us/iaas/api/specs/262828676ddc987c55151766aa2127c9c73d8a81ad9625e1214e80e7cba22d26.yaml'
    ],
    'jms-utils': [
        'https://docs.oracle.com/en-us/iaas/api/specs/fa4258099975c15660254dbd2ba6c584173b6610144b9157d5731fc976e2eb89.yaml'
    ],
    'kafka': [
        'https://docs.oracle.com/en-us/iaas/api/specs/34e70749383ab7899a1bee55aadf7900d085587a47b0bc9d77ed59ae6c101e6d.yaml'
    ],
    'key': [
        'https://docs.oracle.com/en-us/iaas/api/specs/6650b193f50d51919ae1a5f31b525097c777bb9e61575a82b12bf5a5fa5c1dea.yaml'
    ],
    'language': [
        'https://docs.oracle.com/en-us/iaas/api/specs/adb3a186e5819a0420c88de5187f9efa91a143c6564545e588f0adf493273cae.yaml'
    ],
    'licensemanager': [
        'https://docs.oracle.com/en-us/iaas/api/specs/e63cf0b5f8ae65726abb49f5975658a92a63da7df5caa1c6cbe6a940d9333ac5.yaml'
    ],
    'limits': [
        'https://docs.oracle.com/en-us/iaas/api/specs/2d638eaf46afc867c116a0d1e8a1c147ddef4ef8b1cef748396ff188b53b0bcd.yaml'
    ],
    'loadbalancer': [
        'https://docs.oracle.com/en-us/iaas/api/specs/b6419140fb4ac827445b4aac56633924a590bd456e678229e1c16c1afbcb7227.yaml'
    ],
    'logan-api-spec': [
        'https://docs.oracle.com/en-us/iaas/api/specs/deab48bca0bf6a50f7f3249d3ea22f8c74709766d0bd85f4f641158297df9301.yaml'
    ],
    'logging-dataplane': [
        'https://docs.oracle.com/en-us/iaas/api/specs/b5e593674a1320aba186c2ad796b0b8bea99c3dc847ba47dfb7246ccb9f4dc81.yaml'
    ],
    'logging-management': [
        'https://docs.oracle.com/en-us/iaas/api/specs/699280e1cc4012b0c9035cbada18968fbd16c7e9a42d2630584de8c1d568772d.yaml'
    ],
    'logging-search': [
        'https://docs.oracle.com/en-us/iaas/api/specs/fd5acb9f4afddc0bd60d889427e4e5c00b1fb46c44219453ae87af5b23e0b823.yaml'
    ],
    'lustre': [
        'https://docs.oracle.com/en-us/iaas/api/specs/d951accfce39573f3ffa7134dbb922b3900ba751ecc03408c36740f089505e08.yaml'
    ],
    'managed-access': [
        'https://docs.oracle.com/en-us/iaas/api/specs/f397c9292e6f977d1885091f8a6e9a9c3cdcb882c49d89bc55720e8eec0c02d1.yaml'
    ],
    'management-agent': [
        'https://docs.oracle.com/en-us/iaas/api/specs/62cf5df470cc2301808169ebab7169be5019d2132e942ab267ed8466f2962ca6.yaml'
    ],
    'managementdashboard': [
        'https://docs.oracle.com/en-us/iaas/api/specs/cd52b76554f07c6cbf450d60c5924cf9b0669e86c97cf5023a8939f661eccb67.yaml'
    ],
    'marketplace': [
        'https://docs.oracle.com/en-us/iaas/api/specs/5610b7055ecadc9a892072b09a4984658029c630ca7f33c8669ed31484d1da3d.yaml'
    ],
    'mngdmac': [
        'https://docs.oracle.com/en-us/iaas/api/specs/9ddea3093fd3564bac7128a88f62ab50750d17916eb1a9c18fb85144868ac15d.yaml'
    ],
    'monitoring': [
        'https://docs.oracle.com/en-us/iaas/api/specs/69b9986d0d4ba07ab7f8c49624363def032da8d0c5b981e5dc6cea8a473e309f.yaml'
    ],
    'multicloud-omhub-cp': [
        'https://docs.oracle.com/en-us/iaas/api/specs/15cd29e2863721ca701a6012da8be6398c0793a11f06fc8914ca63a92e6fee95.yaml'
    ],
    'mysql': [
        'https://docs.oracle.com/en-us/iaas/api/specs/ff695bc6bfad32f42ff1b1f2ff2f4a93baf752ccdcde5c863e6c15020302e82e.yaml'
    ],
    'network-firewall': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c9e6d3f0c0ac7cb5be51e2068be4507f2ff44ebea1bd02a7d11cece55945c446.yaml',
        'https://docs.oracle.com/en-us/iaas/api/specs/7e658a16c056df0cfbdad56ffa822bcdf218d64bfbfcd69e621166d281a9ed99.yaml',
    ],
    'networkloadbalancer': [
        'https://docs.oracle.com/en-us/iaas/api/specs/78ad56a04afca985945937d703d0d391f468fbef6049606759dccdd3804b2f9f.yaml'
    ],
    'nosql-database': [
        'https://docs.oracle.com/en-us/iaas/api/specs/12cc3142be3f1a80f0b5ac96581767826a55104bd1ae80465b4ebbbbde27be43.yaml'
    ],
    'notification': [
        'https://docs.oracle.com/en-us/iaas/api/specs/14e5a8c24001383732b20453d9b177ede7ed076f9ad3fb4854c8a85494ba67da.yaml'
    ],
    'objectstorage': [
        'https://docs.oracle.com/en-us/iaas/api/specs/79680c18aae234294d244c4210cc16605bc649c06f641870ab1fd65e31df8f91.yaml'
    ],
    'occ': [
        'https://docs.oracle.com/en-us/iaas/api/specs/b193deba0def3a4cd1118a4ae93d1cb396bb86a2b51c6e4e560790de09e5e6bb.yaml'
    ],
    'occcm': [
        'https://docs.oracle.com/en-us/iaas/api/specs/5e3b9a4301fe6543b194916f93f269f9aa8335d8abac41e3722fb9dc29e3d80c.yaml'
    ],
    'occds': [
        'https://docs.oracle.com/en-us/iaas/api/specs/6ac5f05ed79335096b2e5c6932b3e908e3c9eb7479ccf03f92afd8dd5bb2a92f.yaml'
    ],
    'oce': [
        'https://docs.oracle.com/en-us/iaas/api/specs/e2f95e05ed80584945feff93d4c6a65dc7eabc98f95d08926e3ba270599fc590.yaml'
    ],
    'ocicache': [
        'https://docs.oracle.com/en-us/iaas/api/specs/8e0074e565bbeb41b76feaaaa0e7ddeeb740eeba657ef7acf46594d7beced1d3.yaml'
    ],
    'ocm': [
        'https://docs.oracle.com/en-us/iaas/api/specs/116df44b4c0ea89e6d319573e28ba66409fadf2e643473e3d5da38faffa79e5d.yaml'
    ],
    'opa': [
        'https://docs.oracle.com/en-us/iaas/api/specs/cdbd76a738b92f7c6f1fbe7b0e81a83fcb90927ca2061f39ec38e54560384d5e.yaml'
    ],
    'opensearch': [
        'https://docs.oracle.com/en-us/iaas/api/specs/db7aead90481c47e0d0e3f85d7516754adc899cb5606ea20d87eb9c20d2c0d0e.yaml'
    ],
    'operations-insights': [
        'https://docs.oracle.com/en-us/iaas/api/specs/0aa11df6cc696fae150843d7e55a0d10e673051c701016bb8974ce3aab24f5f3.yaml'
    ],
    'operatoraccesscontrol': [
        'https://docs.oracle.com/en-us/iaas/api/specs/63c37b560d8d45df10328b4bb82b256d04da4df9225c6c95bd7a34f8fb2991e3.yaml'
    ],
    'oracle-api-access-control': [
        'https://docs.oracle.com/en-us/iaas/api/specs/719bd1e3974660c61c71dc28c011d2e310610c413d477fc40a5ea7f9b8df81a9.yaml'
    ],
    'organizations': [
        'https://docs.oracle.com/en-us/iaas/api/specs/42482bab0575813855cb9aab40d788621b430185def5bdc79a47e07bc79cdf01.yaml',
        'https://docs.oracle.com/en-us/iaas/api/specs/b6037ceccb1a82383c4ff722ecd955d5eddf053b35ce2673315106d34adba0bb.yaml',
    ],
    'osmh': [
        'https://docs.oracle.com/en-us/iaas/api/specs/f12715cca1582c05505080aacb6fb6bae6b8859e2b5c6374e34626b23c93111b.yaml'
    ],
    'postgresql': [
        'https://docs.oracle.com/en-us/iaas/api/specs/d4726d6f8c2d8ec868e2437b9b47272afaf451e2548a53f4108d0515ebd74108.yaml'
    ],
    'publisher': [
        'https://docs.oracle.com/en-us/iaas/api/specs/3938126592d6bf89c6de487836ec86a01dbd5f60169ceaef9960866094130d3a.yaml'
    ],
    'queue': [
        'https://docs.oracle.com/en-us/iaas/api/specs/0f4bd2ab04c5a31877daf02850f7ffdd1bf9a743b51ba9a4f4afff5e325a099a.yaml'
    ],
    'recovery-service': [
        'https://docs.oracle.com/en-us/iaas/api/specs/8f9c0a93bb289970624d2aa1c228e764b77b9d767acd456469cc8c844867f7fa.yaml'
    ],
    'registry': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1b407d983d95ab063c67b3d4e85cdb63915ce3be9506b11bbb75958dce0f9760.yaml'
    ],
    'resource-analytics': [
        'https://docs.oracle.com/en-us/iaas/api/specs/cb4e8f91a2dc29176ada20ab09d38f48fcd83e4943d32f7ddf564a0c8b40d5b4.yaml'
    ],
    'resource-discovery-monitoring-control-api': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1519a9c9fba0216ecb3013b91956f5f5cc7aca110c96f3192f7ea8de0e7013e2.yaml'
    ],
    'resource-scheduler': [
        'https://docs.oracle.com/en-us/iaas/api/specs/71e79eba4d71a59cedcf88657dc2ff4974315bef5510d6434ac7ab41b72c6c12.yaml'
    ],
    'resourcemanager': [
        'https://docs.oracle.com/en-us/iaas/api/specs/3996fc34e07b3819881c55c1907b4817d7744a0b7821f28fecef28765e3a9a67.yaml'
    ],
    'rover': [
        'https://docs.oracle.com/en-us/iaas/api/specs/bc82a6be3188c7b03e57bdc1f0d7bc345fff101db5cc63bbd3e9a61d9baea4a3.yaml'
    ],
    's3objectstorage': [
        'https://docs.oracle.com/en-us/iaas/api/specs/937025276d8b42f9f753369a7a4de5db4c6d6034d17a574c3357cb880dc8e603.yaml'
    ],
    'scanning': [
        'https://docs.oracle.com/en-us/iaas/api/specs/dfcab9566c2b7a8c5656c725e400d20b105dfb00c2d7dc80250184ca17d7a4ad.yaml'
    ],
    'search': [
        'https://docs.oracle.com/en-us/iaas/api/specs/b63d06c4cfd359bac0d6d407f3a255c7b03fc403937fe089ab94f759b40e16b1.yaml'
    ],
    'secretmgmt': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c0c869fc4c1c4efd44bf513113ce577a2785863654be723d8e57442a45bb0f9d.yaml'
    ],
    'secretretrieval': [
        'https://docs.oracle.com/en-us/iaas/api/specs/d4bb34135ef3c27764d88e24ec1da31c44a09bbdc5f1c82e76cfb92b709257c3.yaml'
    ],
    'secure-desktops': [
        'https://docs.oracle.com/en-us/iaas/api/specs/a8275f52cebad9a3de0a1b275d5e5e511cd9a6b531113923b8a8d4d85a1d0e9c.yaml'
    ],
    'security-attribute': [
        'https://docs.oracle.com/en-us/iaas/api/specs/3e8451b0041723ae9290c072077d35981f7787ea31c714a04953c8ad404fbfac.yaml'
    ],
    'service-catalog': [
        'https://docs.oracle.com/en-us/iaas/api/specs/7331af53a6aec7acddb0f95d1824085c07535cff7d30f5d256174b4e14523d47.yaml'
    ],
    'serviceconnectors': [
        'https://docs.oracle.com/en-us/iaas/api/specs/23d281837e4b021adcde2cd8fb72e929da1a886c4122c7403ffaa25526a68b61.yaml'
    ],
    'smp': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c47bfe381302303d15621bf56241be88a7c3536563543bf5edefb5dab39b0401.yaml'
    ],
    'speech': [
        'https://docs.oracle.com/en-us/iaas/api/specs/3307ec96a711363413aaa9d52287a8ba05676b811185290f2f7e6fcdf70f8ed0.yaml'
    ],
    'sqlwatch': [
        'https://docs.oracle.com/en-us/iaas/api/specs/948723f996837d9988ac666574b04182357c2048ac3a14589327dee4ca31ebf6.yaml'
    ],
    'stack-monitoring': [
        'https://docs.oracle.com/en-us/iaas/api/specs/b91bae309bd8ae0adbc1f7bbd5eb88868f0b7f44d15c8ede08fb3b5bd7681955.yaml'
    ],
    'streaming': [
        'https://docs.oracle.com/en-us/iaas/api/specs/76f58f9e60b8430dab8737840fc228ef1ea6a0aba5e2128532ed5313deb4928d.yaml'
    ],
    'threat-intel': [
        'https://docs.oracle.com/en-us/iaas/api/specs/17d2201ee8fa40c5d12f2d532a9d279886d09cc2e7bcc6f6f8e8056519be9c01.yaml'
    ],
    'usage': [
        'https://docs.oracle.com/en-us/iaas/api/specs/bf75f6b8268e19a39856ea6941bb40b77a94d1c92b9e2dca3a31e6787f4331d9.yaml'
    ],
    'usage-proxy': [
        'https://docs.oracle.com/en-us/iaas/api/specs/923c4c9e7faf08854042f276c1ca058bf5c0d7901ddbf9c52717a1816a0e8d82.yaml'
    ],
    'vision': [
        'https://docs.oracle.com/en-us/iaas/api/specs/3d504bf6852838dd3bff5ec4bc3c280a9227d9addb79c06cfd74f8a57e149041.yaml'
    ],
    'visual-builder': [
        'https://docs.oracle.com/en-us/iaas/api/specs/c14601888837a0732ce02b8ad7b1fd941cab60ec5a1de80323783260478bd597.yaml'
    ],
    'visual-builder-studio': [
        'https://docs.oracle.com/en-us/iaas/api/specs/5ba0589be6a63a667b5566f13752fb38c3b6b4468c404ffe5a154eeaa6176f52.yaml'
    ],
    'vmware': [
        'https://docs.oracle.com/en-us/iaas/api/specs/01c10dd1921041c2ad09070900971ec774ba5fc2dfdc33d7985f96f95cffe3b1.yaml',
        'https://docs.oracle.com/en-us/iaas/api/specs/e3ce298542f2bb1e8db2c0a03163f3037bf75c99762458623147629464ce527c.yaml',
    ],
    'waa': [
        'https://docs.oracle.com/en-us/iaas/api/specs/dc50b70d5c21d1298bd664f84320e70f07773ce71609749110f8da3201c5e45b.yaml'
    ],
    'waas': [
        'https://docs.oracle.com/en-us/iaas/api/specs/7540df5346a0179ee21443879a914e6da69c4546fb6c218100afb7e07b43c548.yaml'
    ],
    'waf': [
        'https://docs.oracle.com/en-us/iaas/api/specs/1d76443ac0b8fb6212e6e3d30033015ab71a10999f69f3bfb3797b0d4f22f813.yaml'
    ],
    'wlms': [
        'https://docs.oracle.com/en-us/iaas/api/specs/e8fef564dd08c35d57daf974e853a3ca0458970812b456487fa37223ed925cf7.yaml'
    ],
    'workrequests': [
        'https://docs.oracle.com/en-us/iaas/api/specs/fd9a71d04923db979595127ae970f7af4bbbc3bd15b085692ea57a119ed77bc2.yaml'
    ],
    'zero-trust-packet-routing': [
        'https://docs.oracle.com/en-us/iaas/api/specs/ce5d6f81f8578e8c4fc7bcb1685884e783b213fe59294db28e0f8595b494dd20.yaml'
    ],
}
