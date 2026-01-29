"""Google Flow 图片下载工具"""

__version__ = "1.0.0"

BROWSER_SCRIPT = '''// Google Flow 全自动提取脚本
// 在浏览器 Console 运行

window.flowAutoCollector = {
    images: new Map(),
    requestCount: 0,
    running: false,
    
    setupInterceptor: function() {
        const self = this;
        const originalFetch = window.fetch;
        
        window.fetch = async function(...args) {
            const response = await originalFetch(...args);
            
            if (args[0] && args[0].includes('searchProjectWorkflows')) {
                self.requestCount++;
                const clone = response.clone();
                try {
                    const data = await clone.json();
                    const workflows = data?.result?.data?.json?.result?.workflows || [];
                    
                    workflows.forEach(wf => {
                        wf.workflowSteps?.forEach(step => {
                            step.mediaGenerations?.forEach(media => {
                                const key = media?.mediaGenerationId?.mediaKey;
                                const url = media?.mediaData?.imageData?.fifeUri;
                                if (key && url) {
                                    self.images.set(key, url);
                                }
                            });
                        });
                    });
                } catch(e) {}
            }
            return response;
        };
    },
    
    autoScroll: async function() {
        this.running = true;
        console.log('🚀 开始自动滚动...\\n');
        
        const container = document.querySelector('[role="main"]') || 
                         document.querySelector('div[style*="overflow"]') ||
                         document.documentElement;
        
        let noChangeCount = 0;
        let lastCount = 0;
        let scrollAttempts = 0;
        
        while (this.running && scrollAttempts < 1000) {
            const currentCount = this.images.size;
            
            if (currentCount !== lastCount) {
                console.log(`📥 已收集 ${currentCount} 张图片 (请求 ${this.requestCount} 次)`);
                noChangeCount = 0;
            } else {
                noChangeCount++;
            }
            
            if (noChangeCount >= 30) {
                console.log('\\n✅ 连续30次无新数据，收集完成！');
                break;
            }
            
            lastCount = currentCount;
            scrollAttempts++;
            
            container.scrollTo({top: container.scrollHeight, behavior: 'smooth'});
            await new Promise(r => setTimeout(r, 2500));
        }
        
        this.running = false;
        console.log(`\\n✅ 收集完成！共 ${this.images.size} 张图片`);
        if (this.images.size > 0) this.export();
    },
    
    export: function() {
        const imageList = Array.from(this.images.entries()).map(([key, url]) => ({key, url}));
        const blob = new Blob([JSON.stringify(imageList, null, 2)], {type: 'application/json'});
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `google_flow_complete_${imageList.length}.json`;
        a.click();
        console.log(`\\n📁 已导出: google_flow_complete_${imageList.length}.json`);
    },
    
    stop: function() {
        if (!this.running) return;
        this.running = false;
        console.log('⏹️  已停止');
        this.export();
    },
    
    start: function() {
        this.setupInterceptor();
        this.autoScroll();
    }
};

flowAutoCollector.start();
console.log('\\n💡 命令: flowAutoCollector.stop() - 手动停止');
'''
