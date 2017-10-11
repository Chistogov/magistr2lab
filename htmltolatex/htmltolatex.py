# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from lxml import etree
from io import StringIO
from lxml.html import fromstring
import lxml.html
from requests import get
import string

class HtmlToLaTeX:    
        
    def start(self):
        input_query = "http://www.intuit.ru/studies/courses/564/420/info"#raw_input("Enter URL: ")
        pages = self.getLections(input_query)
        for t in pages:
            content = self.getLection("http://www.intuit.ru" + t)  
            name = self.getLectionNmae("http://www.intuit.ru" + t)
            self.saveLatex(name, content)
            
    def getLectionNmae(self, URL): 
        raw = get(URL).text
        page = fromstring(raw)
        name = page.xpath('//*[@id="lecture-block"]/div[1]/div/div[1]/span/span/h1')                  
        return name[0].text
        
    def getLection(self, URL): 
        URLS = self.getPages(URL)
        page_text = [];
        for url in URLS:
            raw = get(url).text
            page = fromstring(raw)
            parse_page = ""
            if url == URLS[0]:
                parse_page = page.xpath('//*[@id="lecture-block"]/div[2]/div/div[5]')
            else:
                parse_page = page.xpath('//*[@id="lecture-block"]/div[2]/div/div[2]')
            html = etree.tostring(parse_page[0], pretty_print=True, method="html")   
            html = unicode(html, "utf-8")
            parser = etree.HTMLParser()
            tree   = etree.parse(StringIO(html), parser)
            root = tree.getroot()
            page_text.append(self.tagsToLatex(root))        
        return self.addLaTeXFrame("".join(page_text))
        
    def getLections(self, URL):
        raw = get(URL).text
        page = fromstring(raw)
        parse_page = page.xpath('//*[@id="showcase-list-wrapper-block"]/div/div/div/div[1]/div[1]/h6/a')                                 
        results = []
        for link in parse_page:
            domain = link.get("href")
            if domain: 
                results.append(domain)
        return results
    
    def getPages(self, URL):
        raw = get(URL).text
        page = fromstring(raw)
        parse_page = page.xpath('//*[@id="lecture-block"]/div[2]/div/div[7]/span/a')                             
        results = []
        results.append(URL)
        for link in parse_page:
            domain = link.get("href")
            if domain: 
                results.append("http://www.intuit.ru/" + domain)
        return results
           
    def addLaTeXFrame(self, tex):
        result = []
        result.append("\\documentclass[12pt, a4paper]{article}\n \
\\usepackage{lingmacros}\n \
\\usepackage[margin={75px,50px}]{geometry}\n \
\\usepackage{tree-dvips}\n \
\\usepackage[demo]{graphicx}\n \
\\usepackage[utf8]{inputenc}\n \
\\usepackage[russian]{babel}\n \
\\usepackage{hyperref}\n \
\\usepackage{tabularx,ragged2e}\n \
\\usepackage{spverbatim}\n \
\\newcolumntype{C}{>{\\raggedright\\arraybackslash}X} % centered \"X\" column\n \
\\begin{document}")
        result.append(tex)
        result.append("\\end{document}")
        return "".join(result)

    
    def tagsToLatex(self, html):
        result = []
        if html.text:
            s = string.replace(html.text, '#', '\\#')
            s = string.replace(s, '$', '\\$')
            s = string.replace(s, '%', '\\%')
            s = string.replace(s, '&', '\\&')
            s = string.replace(s, '_', '\\_')
            s = string.replace(s, '{', '\\{')
            s = string.replace(s, '}', '\\}')
            result.append(s)
        for f in html:
            if f.tag in ["body"]:                
                result.append(self.tagsToLatex(f))
            elif f.tag in ["p"]:                
                result.append('%s\\\\' % self.tagsToLatex(f)) 
            elif f.tag in ["h3"]:
                if(f.text):
                    result.append('\\section{%s}' % self.tagsToLatex(f))
            elif f.tag in ["h4"]:
                if(f.text):
                    result.append('\\section{%s}' % self.tagsToLatex(f))
            elif f.tag in ["b"]:
                result.append('\\textbf{%s}' % self.tagsToLatex(f))     
            elif f.tag in ["i"]:
                result.append('\\textit{%s}' % self.tagsToLatex(f))            
            elif f.tag in ["ul", "ol"]:
                result.append('\\begin{itemize} {%s} \\end{itemize}' % self.tagsToLatex(f))
            elif f.tag in ["li"]:
                result.append('\\item{%s}' % self.tagsToLatex(f)) 
            elif f.tag in ["pre"]:
                result.append('\\begin{spverbatim}' + self.tagsToLatex(f) + '\\end{spverbatim}')
            elif f.tag in ["table" or "tbody"]:
                s = ("<table>%s</table>" % self.preparetable(f)) 
                markup = lxml.html.fromstring(s)
                tbl = []
                rows = markup.cssselect("tr")
                for row in rows:
                    tbl.append(list())
                    for td in row.cssselect("td"):
                        tbl[-1].append(td.text_content())
                    for td in row.cssselect("th"):
                        tbl[-1].append(td.text_content())
                result.append(self.arrayToTexTeable(tbl))
            elif f.tag in ["span", "a", "br"]:
                result.append(self.tagsToLatex(f)) 
            elif f.tag in ["div"]:
                result.append(self.tagsToLatex(f))
            elif f.tag in ["img"]:
                for att in f.attrib.keys():
                    if att =='src':
                        result.append("\\bigbreak \\href{http://www.intuit.ru/%s} \
                        {\\includegraphics{image}}\\\\" % f.attrib[att])                         
            else:
                print "!NotSupported!"
                print('tag',f.tag)
                print('text',f.text)
                print('tail',f.tail)
                print('attrib',f.attrib)

            if f.tail:
                s = string.replace(f.tail, '#', '\\#')
                s = string.replace(s, '$', '\\$')
                s = string.replace(s, '%', '\\%')
                s = string.replace(s, '&', '\\&')
                s = string.replace(s, '_', '\\_')
                s = string.replace(s, '{', '\\{')
                s = string.replace(s, '}', '\\}')
                result.append(s)
        return "".join(result)
          
    def preparetable(self, html):
        result = []
        if html.text:
            s = string.replace(html.text, '#', '\\#')
            s = string.replace(s, '$', '\\$')
            s = string.replace(s, '%', '\\%')
            s = string.replace(s, '&', '\\&')
            s = string.replace(s, '_', '\\_')
            s = string.replace(s, '{', '\\{')
            s = string.replace(s, '}', '\\}')
            result.append(s)
        for f in html:
            if f.tag in ["table" or "tbody"]:
                result.append("<table>%s</table>" % self.preparetable(f))
            elif f.tag in ["tr"]:
                result.append("<tr>%s</tr>" % self.preparetable(f))
            elif f.tag in ["td"]:
                result.append("<td>%s</td>" % self.preparetable(f))
            elif f.tag in ["th"]:
                result.append("<th>%s</th>" % self.preparetable(f))
            elif f.tag in ["div"]:
                result.append(self.preparetable(f))
            elif (f.text):
                result.append(f.text + self.preparetable(f))
            if f.tail:
                s = string.replace(f.tail, '#', '\\#')
                s = string.replace(s, '$', '\\$')
                s = string.replace(s, '%', '\\%')
                s = string.replace(s, '&', '\\&')
                s = string.replace(s, '_', '\\_')
                s = string.replace(s, '{', '\\{')
                s = string.replace(s, '}', '\\}')
                result.append(s)
                
        return "".join(result)
        
    def arrayToTexTeable(self, array):
        result = []
        result.append("\\begin{table}[!ht] \
\\setlength\\extrarowheight{2pt} \
\\begin{tabularx}{\\textwidth}{|C|C|C|C|C|C|C|} \\hline")
        for g in array:
            if len(g)>1:
                for h in g:
                    if (g[-1] != h):
                        result.append(h + "&")
                    else: 
                        result.append(h)                
            else:
                result.append("\\multicolumn{2}{|c|}{%s}" % g[0])
            result.append("\\\\ \\hline")
        result.append("\\end{tabularx} \
        \\end{table}")
        return "".join(result) 
    
    def saveLatex(self, name, content):
        try:
            file = open(name + '.tex')
        except IOError as e:
            print('File not exists')
            with open(name + ".tex","w") as out:
                out.write(content.encode("utf-8"))
        else:
            with open(name + ".tex","w") as out:  
                out.seek(0)
                out.truncate()                
                out.write(content.encode("utf-8"))   
            
if __name__ == "__main__":
    program = HtmlToLaTeX()
    program.start()