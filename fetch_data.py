            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "type_1"})
            
            # 💡 [교정] table이 일시적으로 안 잡히더라도 break로 종료하지 않고, 
            # 다음 페이지로 안전하게 넘어가도록(continue) 수정하여 수집 누락을 차단합니다.
            if not table:
                print(f"⚠️ {page}페이지에서 테이블을 로드하지 못했습니다. 건너뜁니다.")
                continue
                
            rows = table.find_all("tr")
            
            for row in rows:
                cols = row.find_all("td")
                
                # 유효한 행 검사
                if len(cols) > 0:
                    theme_tag = cols[0].find("a")
                    
                    # 'themeId=' 주소가 포함된 실제 테마 데이터 행만 정확히 정밀 타격
                    if theme_tag and "themeId=" in theme_tag.get('href', ''):
                        theme_name = theme_tag.text.strip()
                        
                        # 1. 등락률 정제 및 float 변환
                        rate_text = cols[1].text.strip()
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '').replace('\n', '').replace('\t', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue # 숫자가 아니면 스킵
                            
                        # 2. 대장주 추출 (종목 링크인 'item.nhn?code=' 기반 검색)
                        stock_name = "종목 정보 없음"
                        for col in cols[4:]:
                            stock_tag = col.find("a")
                            if stock_tag and "item.nhn?code=" in stock_tag.get('href', ''):
                                stock_name = stock_tag.text.strip()
                                break
                        
                        themes.append(theme_name)
                        stocks.append(stock_name)
                        rates.append(rate)
