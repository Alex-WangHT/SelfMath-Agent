from math_ocr_system import MathOCRSystem
import json
import os


def main():
    print("=" * 60)
    print("数学习题集OCR题库扫描系统 - 最小演示")
    print("=" * 60)
    
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n⚠️  请先配置 API Key:")
        print("1. 复制 .env.example 为 .env")
        print("2. 将 SILICONFLOW_API_KEY 替换为你的硅基流动API密钥")
        print("3. API密钥可在 https://cloud.siliconflow.cn 获取")
        return
    
    system = MathOCRSystem()
    
    print("\n📋 功能选项:")
    print("1. 处理PDF文件并提取题目")
    print("2. 搜索已存储的题目")
    print("3. 查看所有已存储的题目")
    print("4. 退出")
    
    choice = input("\n请选择操作 (1/2/3/4): ").strip()
    
    if choice == "1":
        pdf_path = input("\n请输入PDF文件路径: ").strip()
        
        if not os.path.exists(pdf_path):
            print(f"❌ 文件不存在: {pdf_path}")
            return
        
        start_page_input = input("起始页码 (默认0): ").strip()
        start_page = int(start_page_input) if start_page_input else 0
        
        end_page_input = input("结束页码 (默认全部): ").strip()
        end_page = int(end_page_input) if end_page_input else None
        
        print(f"\n🚀 开始处理 PDF: {pdf_path}")
        
        try:
            questions = system.process_pdf(pdf_path, start_page, end_page)
            
            if questions:
                print(f"\n✅ 成功提取 {len(questions)} 道题目!")
                print("\n📄 提取的题目预览:")
                print("-" * 60)
                
                for i, q in enumerate(questions[:3]):
                    print(f"\n--- 题目 {i + 1} ---")
                    print(f"题号: {q.get('question_number', 'N/A')}")
                    print(f"内容: {q.get('question_content', 'N/A')[:200]}...")
                
                if len(questions) > 3:
                    print(f"\n... 还有 {len(questions) - 3} 道题目")
            else:
                print("⚠️  未提取到任何题目")
        
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "2":
        query = input("\n请输入搜索关键词: ").strip()
        n_results_input = input("返回结果数量 (默认5): ").strip()
        n_results = int(n_results_input) if n_results_input else 5
        
        results = system.search_questions(query, n_results)
        
        if results:
            print(f"\n🔍 找到 {len(results)} 个相关题目:")
            print("-" * 60)
            
            for i, r in enumerate(results):
                print(f"\n--- 结果 {i + 1} ---")
                print(f"ID: {r['id']}")
                print(f"内容: {r['content']}")
                print(f"来源: {r['metadata'].get('source', 'N/A')}")
        else:
            print("⚠️  未找到相关题目")
    
    elif choice == "3":
        questions = system.get_all_questions()
        
        if questions:
            print(f"\n📚 共有 {len(questions)} 道已存储的题目:")
            print("-" * 60)
            
            for i, q in enumerate(questions[:10]):
                print(f"\n--- 题目 {i + 1} ---")
                print(f"ID: {q['id']}")
                print(f"内容: {q['content'][:150]}...")
                print(f"来源: {q['metadata'].get('source', 'N/A')}")
            
            if len(questions) > 10:
                print(f"\n... 还有 {len(questions) - 10} 道题目")
        else:
            print("⚠️  数据库中暂无题目")
    
    elif choice == "4":
        print("\n👋 再见!")
        return
    
    else:
        print("❌ 无效选项")


if __name__ == "__main__":
    main()
